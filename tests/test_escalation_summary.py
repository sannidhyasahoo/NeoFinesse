"""
tests/test_escalation_summary.py
================================
Unit tests for EscalationSummaryService, Human Review Handoff, investigation timelines,
missing evidence categorizations, and fail-safe deterministic generation.
"""
from pathlib import Path
import json
import pytest

from neofinesse.services.escalation_summary_service import (
    EscalationSummaryService,
    HumanReviewHandoff,
    MissingEvidenceCategory,
    InvestigationStep,
)


@pytest.fixture
def sample_var008_scenario():
    return {
        "scenario_id": "VAR-008_WRONG_DATE_DECOY",
        "case_id": "CASE-008",
        "settlement_id": "setl_scen_008_2140",
        "category": "Settlement RCA",
        "expected_outcome": "ESCALATE",
        "expected_amount_inr": 7716.8,
        "actual_bank_credit_inr": 11716.8,
        "variance_inr": 4000.0,
        "variance_paise": 400000,
        "primary_cause": "UNEXPLAINED",
        "evidence_nodes": [],
        "rejected_decoys": [
            {
                "evidence_id": "E-008_DECOY",
                "entity_type": "REFUND",
                "entity_key": "ref_scen_008_outdated",
                "amount_inr": 4000.0,
                "relationship_path": "Refund ref_scen_008_outdated -> Payment pay_old_301 -> Settlement setl_scen_008_2140",
                "source_file": "refunds.csv",
                "sheet": "Refunds_FY24_Archive",
                "row": 31,
                "cell": "F31",
                "record_hash": "a601b489d93d3511c5d11be95731c96e2415b311830f6e54186021447399bce6",
                "status": "REJECTED",
                "rejection_reason": "Temporal Cut-off Violation: Refund timestamp is 14 days prior to settlement batch cut-off",
                "lesson": "Plausible != Proven. System rejects out-of-window decoys and safely escalates.",
            }
        ],
        "constraint_checks": [
            {"name": "Monetary Balance", "description": "Candidate matched amount", "status": "PASS", "rule": "amount_heuristic"},
            {"name": "Settlement Membership", "description": "Linked payment verified", "status": "PASS", "rule": "foreign_key_verified"},
            {"name": "Temporal Window", "description": "VIOLATION: Event occurred 14 days prior (limit: 48h)", "status": "FAIL", "rule": "temporal_horizon_exceeded"},
            {"name": "State Validity", "description": "State verified", "status": "PASS", "rule": "state_terminal_success"},
            {"name": "Provenance Chain", "description": "Stale batch", "status": "FAIL", "rule": "stale_provenance"},
        ],
        "ai_hypothesis": {
            "proposed_explanation": "Variance of ₹4000.00 caused by refund ref_scen_008_outdated.",
            "tools_requested": ["retrieve_entities()", "query_temporal_window()"],
            "ai_confidence": "LOW (0.31)",
        },
        "verifier_outcome": {
            "verdict": "REJECTED",
            "constraints_passed": 3,
            "constraints_total": 5,
            "final_decision": "ESCALATE",
        },
    }


def test_var008_handoff_summary_generation(sample_var008_scenario):
    handoff: HumanReviewHandoff = EscalationSummaryService.generate_handoff_summary(sample_var008_scenario)

    assert handoff.case_id == "CASE-008"
    assert handoff.scenario_id == "VAR-008_WRONG_DATE_DECOY"
    assert handoff.settlement_id == "setl_scen_008_2140"
    assert handoff.variance_inr == 4000.0
    assert handoff.unresolved_variance_inr == 4000.0
    assert handoff.severity == "HIGH"

    # Why escalated contains temporal reason
    assert "cutoff" in handoff.why_escalated.lower() or "temporal" in handoff.why_escalated.lower()
    assert "similarity" in handoff.why_could_not_close.lower() or "temporal" in handoff.why_could_not_close.lower()

    # Recommended human action
    assert "subsequent settlement cycle" in handoff.recommended_human_action.lower() or "adjustment" in handoff.recommended_human_action.lower()

    # Rejected decoy present
    assert len(handoff.rejected_evidence) == 1
    assert handoff.rejected_evidence[0]["evidence_id"] == "E-008_DECOY"

    # Failed constraints
    assert len(handoff.failed_constraints) >= 1
    temporal_failed = any(fc["constraint_name"] == "Temporal Window" for fc in handoff.failed_constraints)
    assert temporal_failed is True

    # Missing evidence category identified
    assert len(handoff.missing_evidence) >= 1
    assert any(m.category == MissingEvidenceCategory.OUTSIDE_TIME_WINDOW for m in handoff.missing_evidence)

    # Investigation timeline
    assert len(handoff.investigation_timeline) >= 4
    assert any("Variance Detected" in step.action for step in handoff.investigation_timeline)
    assert any("Candidate Evaluated" in step.action for step in handoff.investigation_timeline)
    assert any("Deterministic Verifier Verdict" in step.action for step in handoff.investigation_timeline)


def test_separation_of_ai_from_deterministic_proof(sample_var008_scenario):
    handoff = EscalationSummaryService.generate_handoff_summary(sample_var008_scenario)

    # AI thought is strictly tagged as hypothesis only
    assert handoff.ai_hypothesis_summary["ai_status"] == "HYPOTHESIS_ONLY_UNCONFIRMED"
    assert "ref_scen_008_outdated" in handoff.ai_hypothesis_summary["hypothesis"]

    # Verifier outcome has terminal authority
    assert handoff.deterministic_verdict["verdict"] == "REJECTED"
    assert handoff.deterministic_verdict["final_status"] == "ESCALATE"


def test_unexplained_variance_fallback():
    minimal_scenario = {
        "case_id": "CASE-999",
        "scenario_id": "VAR-999_MYSTERY",
        "settlement_id": "setl_999",
        "variance_inr": -15000.0,
        "expected_amount_inr": 20000.0,
        "actual_bank_credit_inr": 5000.0,
        "expected_outcome": "ESCALATE",
    }

    handoff = EscalationSummaryService.generate_handoff_summary(minimal_scenario)
    assert handoff.case_id == "CASE-999"
    assert handoff.severity == "CRITICAL"
    assert handoff.unresolved_variance_inr == 15000.0
    assert "completely unexplained" in handoff.why_escalated.lower() or "no candidate" in handoff.why_escalated.lower()
    assert len(handoff.missing_evidence) >= 1
    assert handoff.missing_evidence[0].category == MissingEvidenceCategory.MISSING_SOURCE_RECORD
