import React from "react";
import { Scenario, EvidenceNode } from "@/types";
import { AlertOctagon, ShieldAlert, CheckCircle, ArrowRight, UserCheck, FileText, ChevronRight } from "lucide-react";
import { benchmarkData } from "@/data/benchmarkData";

interface EscalationQueueProps {
  scenario: Scenario;
  onViewSource?: (evidence: EvidenceNode) => void;
  onOpenReviewDossier?: (scenario: Scenario) => void;
  onSelectScenario?: (scenarioId: string) => void;
}

export default function EscalationQueue({
  scenario,
  onViewSource,
  onOpenReviewDossier,
  onSelectScenario,
}: EscalationQueueProps) {
  const isEscalated = scenario.expected_outcome === "ESCALATE";
  const varFormatted =
    scenario.variance_inr < 0
      ? `-₹${Math.abs(scenario.variance_inr).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
      : `+₹${scenario.variance_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;

  const rejectedDecoys = scenario.rejected_decoys || [];
  const candidateEvidence = scenario.evidence_nodes || [];
  const allRelatedEvidence = [...candidateEvidence, ...rejectedDecoys];

  // All escalated scenarios in the dataset
  const allEscalatedScenarios = benchmarkData.scenarios.filter((s) => s.expected_outcome === "ESCALATE");

  return (
    <div className="space-y-6">
      {/* Hero Banner with Direct Review Action */}
      <div className="bg-white rounded-3xl border border-ash p-6 sm:p-8 space-y-6 shadow-sm">
        {isEscalated ? (
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-ash/50 pb-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center">
                <AlertOctagon className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-serif text-2xl text-off-black">
                  Cases Sent to Human Review &bull; <span className="text-lake-blue">{scenario.case_id}</span>
                </h3>
                <p className="text-xs font-mono text-smoke mt-0.5">
                  When the system can&rsquo;t fully prove an explanation, it sends the case here with a complete investigation handoff rather than guessing.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 self-start sm:self-auto">
              <div className="px-4 py-2 bg-parchment rounded-2xl border border-ash text-right">
                <div className="text-[10px] uppercase font-mono text-smoke">Unresolved Amount</div>
                <div className="text-lg font-mono font-bold text-rose-600">{varFormatted}</div>
              </div>

              {onOpenReviewDossier && (
                <button
                  onClick={() => onOpenReviewDossier(scenario)}
                  className="px-5 py-3.5 bg-rose-600 hover:bg-rose-700 text-white rounded-2xl text-xs font-mono font-bold uppercase tracking-wider transition-all flex items-center gap-2 shadow-md hover:scale-102"
                >
                  <FileText className="w-4 h-4" />
                  <span>Review Handoff</span>
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-ash/50 pb-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-600 flex items-center justify-center">
                <CheckCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-serif text-2xl text-off-black">
                  Case Resolved &bull; <span className="text-lake-blue">{scenario.case_id}</span>
                </h3>
                <p className="text-xs font-mono text-smoke mt-0.5">
                  This case was successfully proven and resolved automatically. It is not in the human review queue.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Forensic Audit Details */}
        <div className="space-y-4">
          <div className="text-xs uppercase font-mono font-bold text-off-black tracking-wider flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-600" />
            <span>Why was this case not closed automatically?</span>
          </div>

          <div className="p-4 bg-parchment rounded-2xl border border-ash/70 space-y-3">
            <p className="text-xs font-mono text-off-black leading-relaxed">
              {scenario.primary_cause || "No valid explanation satisfies all five verification checks."}
            </p>

            <div className="space-y-2 pt-2 border-t border-ash/40">
              <div className="text-[10px] uppercase font-mono text-smoke font-medium">
                Checks that failed:
              </div>
              {(scenario.verifier_constraints || [])
                .filter((c) => c.status === "FAIL")
                .map((c, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-rose-50/70 rounded-xl border border-rose-200 text-xs font-mono text-rose-900 flex items-start gap-2"
                  >
                    <span className="w-2 h-2 rounded-full bg-rose-500 mt-1.5 shrink-0" />
                    <div>
                      <strong>{c.constraint_name}:</strong> {c.details}
                    </div>
                  </div>
                ))}
              {(scenario.verifier_constraints || []).filter((c) => c.status === "FAIL").length === 0 && (
                <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs font-mono text-emerald-900">
                  All constraints passed. Case is resolved without escalation.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Attached Source Evidence Records (Decoys / Candidates) */}
        {allRelatedEvidence.length > 0 && (
          <div className="space-y-3">
            <div className="text-xs uppercase font-mono font-bold text-off-black tracking-wider">
              Attached Evidence Records ({allRelatedEvidence.length})
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {allRelatedEvidence.map((ev, idx) => {
                const isDecoy = ev.status === "REJECTED";
                return (
                  <div
                    key={idx}
                    className={`p-3.5 rounded-2xl border text-xs font-mono flex flex-col justify-between space-y-2 ${
                      isDecoy
                        ? "bg-rose-50/50 border-rose-200 text-rose-950"
                        : "bg-parchment border-ash text-off-black"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-bold text-lake-blue">
                        {ev.evidence_id} &bull; {ev.entity_type}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded-pill text-[10px] font-bold uppercase ${
                          isDecoy ? "bg-rose-200 text-rose-900" : "bg-emerald-100 text-emerald-900"
                        }`}
                      >
                        {isDecoy ? "✕ Decoy" : "✓ Candidate"}
                      </span>
                    </div>

                    <div className="text-[11px] text-smoke truncate">
                      {ev.source_file} &bull; {ev.sheet}!{ev.cell}
                    </div>

                    {isDecoy && ev.rejection_reason && (
                      <div className="text-[10px] text-rose-800 italic">
                        {ev.rejection_reason}
                      </div>
                    )}

                    {onViewSource && (
                      <button
                        onClick={() => onViewSource(ev)}
                        className="self-start px-3 py-1 mt-1 bg-white hover:bg-off-black hover:text-white border border-ash rounded-pill text-[10px] font-bold uppercase tracking-wider transition-all flex items-center gap-1.5 shadow-sm"
                      >
                        <span>View Source Cell ({ev.cell}) &rarr;</span>
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Recommended System Action */}
        <div className="p-4 bg-periwinkle-mist/40 rounded-2xl border border-ash flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="text-[10px] uppercase font-mono text-smoke font-medium">
              Next Action
            </div>
            <div className="text-xs font-mono font-semibold text-off-black">
              Assign to a human auditor. Full source file evidence and investigation steps are attached.
            </div>
          </div>

          <div className="flex items-center gap-2">
            {onOpenReviewDossier && (
              <button
                onClick={() => onOpenReviewDossier(scenario)}
                className="px-4 py-2 bg-rose-600 text-white hover:bg-rose-700 rounded-btn text-xs font-mono uppercase tracking-wider transition-colors flex items-center gap-1.5 shadow-sm font-semibold"
              >
                <FileText className="w-3.5 h-3.5" /> Open Full Dossier
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Full Human Review Queue Table (All Escalated Scenarios) */}
      <div className="bg-white rounded-3xl border border-ash p-6 sm:p-8 space-y-4 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-ash/40 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 text-rose-600" />
              <h3 className="font-serif text-xl sm:text-2xl text-off-black">
                Active Human Review Queue ({allEscalatedScenarios.length} Cases)
              </h3>
            </div>
            <p className="text-xs font-mono text-smoke mt-0.5">
              Click &ldquo;Review Handoff&rdquo; on any case to inspect its evidence trail, hypotheses considered, rejected decoys, and recommended next steps.
            </p>
          </div>
          <span className="px-3 py-1 rounded-pill bg-rose-100 text-rose-800 text-xs font-mono font-bold uppercase self-start sm:self-auto">
            Zero Guessing &bull; 0% False Closure
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="bg-parchment/70 border-b border-ash text-[11px] uppercase tracking-wider text-smoke font-semibold">
                <th className="py-3 px-4">Case ID</th>
                <th className="py-3 px-4">Settlement Batch</th>
                <th className="py-3 px-4">Unresolved Variance</th>
                <th className="py-3 px-4">Primary Failure Reason</th>
                <th className="py-3 px-4">Decoys / Checks</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ash/40">
              {allEscalatedScenarios.map((scen, idx) => {
                const isCurrent = scen.scenario_id === scenario.scenario_id;
                const formattedVal =
                  scen.variance_inr < 0
                    ? `-₹${Math.abs(scen.variance_inr).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
                    : `+₹${scen.variance_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;

                const failedCheck =
                  scen.constraint_checks?.find((c) => c.status === "FAIL")?.name ||
                  (scen.rejected_decoys && scen.rejected_decoys.length > 0 ? "Decoy Rejected (Temporal/FK)" : "Unexplained Discrepancy");

                return (
                  <tr
                    key={idx}
                    className={`transition-colors ${
                      isCurrent ? "bg-rose-50/50 font-medium" : "hover:bg-parchment/40"
                    }`}
                  >
                    <td className="py-3 px-4">
                      <div className="font-bold text-off-black flex items-center gap-1.5">
                        <span className="text-lake-blue">{scen.case_id}</span>
                        {isCurrent && (
                          <span className="px-1.5 py-0.2 rounded bg-rose-200 text-rose-900 text-[9px] font-bold">
                            CURRENT
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-smoke truncate max-w-[140px]">{scen.scenario_id}</div>
                    </td>

                    <td className="py-3 px-4 text-graphite font-medium">
                      {scen.settlement_id}
                    </td>

                    <td className="py-3 px-4 font-bold text-rose-600">
                      {formattedVal}
                    </td>

                    <td className="py-3 px-4 text-graphite text-[11px] max-w-[200px] truncate">
                      {failedCheck}
                    </td>

                    <td className="py-3 px-4 text-smoke text-[11px]">
                      {scen.rejected_decoys?.length ? `${scen.rejected_decoys.length} Decoy(s) Rejected` : "0 candidates"}
                    </td>

                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        {onOpenReviewDossier && (
                          <button
                            onClick={() => onOpenReviewDossier(scen)}
                            className="px-3 py-1.5 bg-off-black hover:bg-rose-600 text-white rounded-pill text-[10px] font-mono uppercase tracking-wider font-bold transition-all shadow-sm"
                          >
                            Review
                          </button>
                        )}
                        {onSelectScenario && !isCurrent && (
                          <button
                            onClick={() => onSelectScenario(scen.scenario_id)}
                            className="px-2.5 py-1.5 bg-parchment hover:bg-ash/40 border border-ash text-off-black rounded-pill text-[10px] font-mono transition-all"
                            title="Switch workspace view to this scenario"
                          >
                            Select
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
