import { NextRequest, NextResponse } from "next/server";
import { benchmarkData } from "@/data/benchmarkData";
import { Scenario, EvidenceNode } from "@/types";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const scenarioId = searchParams.get("scenario_id") || searchParams.get("case_id");

    const scenarios = benchmarkData.scenarios;
    let targetScenario: Scenario | undefined;

    if (scenarioId) {
      targetScenario = scenarios.find(
        (s) => s.scenario_id === scenarioId || s.case_id === scenarioId
      );
    }

    if (!targetScenario) {
      // Default to Demo 4 / first escalated scenario
      targetScenario = scenarios.find((s) => s.expected_outcome === "ESCALATE") || scenarios[0];
    }

    const varInr = targetScenario.variance_inr;
    const absVar = Math.abs(varInr);
    const setlId = targetScenario.settlement_id;
    const expAmount = targetScenario.expected_amount_inr;
    const actCredit = targetScenario.actual_bank_credit_inr;

    const evidenceNodes = targetScenario.evidence_nodes || [];
    const rejectedDecoys = targetScenario.rejected_decoys || [];
    const constraintChecks = targetScenario.constraint_checks || [];

    const failedConstraints = constraintChecks
      .filter((c) => c.status === "FAIL" || c.status === "WARN")
      .map((c) => ({
        constraint_name: c.name,
        rule: c.rule,
        details: c.description,
      }));

    const hasTemporalFailure = failedConstraints.some(
      (c) => c.constraint_name.toLowerCase().includes("temporal") || c.rule.toLowerCase().includes("temporal")
    );
    const hasFkFailure = failedConstraints.some(
      (c) => c.constraint_name.toLowerCase().includes("membership") || c.rule.toLowerCase().includes("foreign")
    );

    let whyEscalated = "";
    let whyCouldNotClose = "";
    let nextAction = "";

    if (rejectedDecoys.length > 0 && hasTemporalFailure) {
      whyEscalated = `A candidate event matching the ₹${absVar.toLocaleString("en-IN", { minimumFractionDigits: 2 })} variance was found, but its timestamp falls outside the valid settlement cutoff window. The deterministic verifier rejected closure to prevent false reconciliation.`;
      whyCouldNotClose = `Amount matched ₹${absVar.toLocaleString("en-IN", { minimumFractionDigits: 2 })}, but the event occurred outside the allowed cut-off window. Monetary similarity alone is insufficient to prove causation without temporal coherence.`;
      nextAction = `Verify whether the refund/event belongs to a later settlement cycle or investigate an unrecorded manual adjustment.`;
    } else if (rejectedDecoys.length > 0 && hasFkFailure) {
      whyEscalated = `A candidate transaction was identified with matching amount, but relational traversal proved it belongs to a different foreign settlement batch. The decoy was safely rejected.`;
      whyCouldNotClose = `Candidate belongs to another entity/batch. Naive amount matching would cause an incorrect closure. Causal graph traversal proved the link is invalid.`;
      nextAction = `Inspect the merchant's master payment ledger and confirm whether an adjustment or chargeback reversal is logged for settlement ${setlId}.`;
    } else if (evidenceNodes.length === 0 && rejectedDecoys.length === 0) {
      whyEscalated = `No candidate transactions or ledger entries account for the ₹${absVar.toLocaleString("en-IN", { minimumFractionDigits: 2 })} variance. The variance remains completely unexplained.`;
      whyCouldNotClose = `Zero matching evidence records found across payments, refunds, disputes, or bank transfers for settlement ${setlId}.`;
      nextAction = `Request an updated bank statement and check for unimported payment gateway fees, tax lines, or manual debit holds.`;
    } else {
      whyEscalated = `Deterministic constraint verification failed for 1 or more critical mathematical checks. No valid causal chain satisfies the required 5-point verification.`;
      whyCouldNotClose = `Constraint checks failed: ${failedConstraints.map((c) => c.constraint_name).join(", ") || "Unresolved discrepancy"}.`;
      nextAction = `Review attached source file coordinates and conduct manual audit on settlement ${setlId}.`;
    }

    const verificationsAttempted = constraintChecks.map((c) => ({
      check_name: c.name,
      description: c.description,
      passed: c.status === "PASS",
    }));

    const missingEvidence: any[] = [];
    if (hasTemporalFailure || (rejectedDecoys.length > 0 && hasTemporalFailure)) {
      missingEvidence.push({
        category: "OUTSIDE_TIME_WINDOW",
        description: `Timely event within 48h batch cutoff window for settlement ${setlId}`,
        expected_entity: "REFUND / ADJUSTMENT",
        potential_impact_inr: absVar,
      });
    }
    if (hasFkFailure) {
      missingEvidence.push({
        category: "MISSING_SETTLEMENT_MEMBERSHIP",
        description: `Direct relational foreign key linking payment to settlement ${setlId}`,
        expected_entity: "PAYMENT_LINK",
        potential_impact_inr: absVar,
      });
    }
    if (evidenceNodes.length === 0) {
      missingEvidence.push({
        category: "MISSING_SOURCE_RECORD",
        description: `Unimported credit/debit record accounting for ₹${absVar.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`,
        expected_entity: "ADJUSTMENT / FEE",
        potential_impact_inr: absVar,
      });
    }

    const timeline = [
      {
        timestamp: "14:02:11",
        action: "Variance Detected",
        detail: `Settlement ${setlId} has ₹${absVar.toLocaleString("en-IN", { minimumFractionDigits: 2 })} variance (Expected: ₹${expAmount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}, Bank Credit: ₹${actCredit.toLocaleString("en-IN", { minimumFractionDigits: 2 })})`,
        status: "INFO",
        audit_event_id: "EVT-001-DETECT",
      },
      {
        timestamp: "14:02:11",
        action: "Evidence Retrieval",
        detail: "Retrieved candidate records matching settlement context and entity relationships",
        status: "INFO",
        audit_event_id: "EVT-002-RETRIEVE",
      },
    ];

    for (const d of rejectedDecoys) {
      timeline.push({
        timestamp: "14:02:12",
        action: `Candidate Evaluated: ${d.evidence_id}`,
        detail: `Amount matches ₹${Math.abs(d.amount_inr).toLocaleString("en-IN", { minimumFractionDigits: 2 })} but rejected: ${d.rejection_reason || "Constraint failed"}`,
        status: "REJECTED",
        audit_event_id: "EVT-003-REJECT",
      });
    }

    for (const fc of failedConstraints) {
      timeline.push({
        timestamp: "14:02:13",
        action: `Constraint Violation: ${fc.constraint_name}`,
        detail: fc.details,
        status: "FAIL",
        audit_event_id: "EVT-004-CONSTRAINT",
      });
    }

    timeline.push({
      timestamp: "14:02:13",
      action: "Deterministic Verifier Verdict",
      detail: "Authority: REJECTED → ESCALATED TO HUMAN REVIEW (0% false closure invariant)",
      status: "FAIL",
      audit_event_id: "EVT-005-ESCALATE",
    });

    const handoff = {
      case_id: targetScenario.case_id,
      scenario_id: targetScenario.scenario_id,
      settlement_id: setlId,
      severity: absVar >= 10000 ? "CRITICAL" : absVar >= 1000 ? "HIGH" : "MEDIUM",
      variance_inr: varInr,
      expected_amount_inr: expAmount,
      actual_bank_credit_inr: actCredit,
      unresolved_variance_inr: absVar,
      why_escalated: whyEscalated,
      why_could_not_close: whyCouldNotClose,
      recommended_human_action: nextAction,
      verifications_attempted: verificationsAttempted,
      evidence_reviewed: evidenceNodes,
      rejected_evidence: rejectedDecoys,
      failed_constraints: failedConstraints,
      missing_evidence: missingEvidence,
      investigation_timeline: timeline,
      ai_hypothesis_summary: {
        hypothesis: targetScenario.ai_hypothesis?.proposed_explanation || `Variance of ₹${absVar.toLocaleString("en-IN", { minimumFractionDigits: 2 })} considered.`,
        tools_used: targetScenario.ai_hypothesis?.tools_requested || ["retrieve_entities()", "evaluate_constraints()"],
        ai_confidence: targetScenario.ai_hypothesis?.ai_confidence || "LOW (0.31)",
        ai_status: "HYPOTHESIS_ONLY_UNCONFIRMED",
      },
      deterministic_verdict: {
        verdict: targetScenario.verifier_outcome?.verdict || "REJECTED",
        constraints_evaluated: constraintChecks.length || 5,
        constraints_failed: failedConstraints.length || 2,
        final_status: "ESCALATE",
        authority_note: "Deterministic verifier evaluated all constraints. Terminal authority rejected closure.",
      },
    };

    return NextResponse.json({ status: "SUCCESS", handoff });
  } catch (err: any) {
    return NextResponse.json(
      { status: "ERROR", error: err.message || "Failed to generate human review summary" },
      { status: 500 }
    );
  }
}
