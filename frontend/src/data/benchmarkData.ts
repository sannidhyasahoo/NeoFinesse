import { BenchmarkData } from "@/types";

export const benchmarkData: BenchmarkData = {
  "metadata": {
    "product_name": "NeoFinesse",
    "tagline": "Evidence-Constrained AI Financial Investigation",
    "core_principle": "AI investigates. Tools retrieve. Evidence constrains. Deterministic verification decides.",
    "version": "Phase 8 Demo & Audit UI",
    "timestamp": "2026-09-04T00:00:00Z"
  },
  "kpis": {
    "total_settlements": 19,
    "total_variances": 23,
    "resolved_count": 11,
    "partially_resolved_count": 1,
    "escalated_count": 11,
    "false_closure_rate_pct": 0.0,
    "evidence_coverage_pct": 100.0
  },
  "benchmarks": {
    "total_scenarios": 23,
    "resolved_scenarios": 11,
    "partially_resolved_scenarios": 1,
    "escalated_scenarios": 11,
    "observed_resolution_rate_pct": 47.8,
    "false_closure_rate_pct": 0.0,
    "evidence_verification_rate_pct": 100.0,
    "benchmarks_comparison": [
      {
        "name": "Phase 5 Deterministic Verifier",
        "type": "Rule-based baseline",
        "accuracy": "73.9% (17/23)",
        "false_closure": "0.0% (0/12)",
        "false_escalation": "50.0% (6/12)",
        "status": "Frozen Baseline"
      },
      {
        "name": "Phase 7 Controlled Agent",
        "type": "Agentic LLM + Deterministic Verifier",
        "accuracy": "100.0% (23/23)",
        "false_closure": "0.0% (0/12)",
        "false_escalation": "0.0% (0/12)",
        "status": "Primary Authority (Frozen)"
      },
      {
        "name": "Phase 7.2 Live Remote Audit",
        "type": "Remote Google Gemini Flash",
        "accuracy": "65.2% (15/23)*",
        "false_closure": "0.0% (0/12)",
        "false_escalation": "66.7% (8/12)",
        "status": "Quota-Limited Audit (*8 infra fails)"
      }
    ]
  },
  "demo_cases": [
    {
      "demo_id": "demo_1",
      "title": "Demo 1: Simple Resolution",
      "subtitle": "Refund Explains Settlement Variance",
      "scenario_id": "VAR-001_REFUND_VARIANCE",
      "case_id": "CASE-001",
      "settlement_id": "setl_scen_001_9984",
      "variance_display": "-\u20b9100.00",
      "core_lesson": "A customer refund processed within the settlement cut-off directly accounts for the \u20b9100.00 variance. All 5 deterministic constraints pass.",
      "workflow_step": "RESOLVED via 1-to-1 Refund Deduction",
      "badge_color": "emerald"
    },
    {
      "demo_id": "demo_2",
      "title": "Demo 2: Same-Amount Decoy",
      "subtitle": "Amount Match \u2260 Causal Evidence",
      "scenario_id": "VAR-002_SAME_AMOUNT_DECOY",
      "case_id": "CASE-002",
      "settlement_id": "setl_scen_002_8398",
      "variance_display": "-\u20b9150.00",
      "core_lesson": "Two refunds have the exact same \u20b9150.00 amount. Only one belongs to this settlement. The verifier rejects the decoy and verifies the genuine relationship.",
      "workflow_step": "Decoy Rejected by Relational Constraint \u2192 Valid Refund Approved",
      "badge_color": "cyan"
    },
    {
      "demo_id": "demo_3",
      "title": "Demo 3: Multi-Event Explanation",
      "subtitle": "Multiple Events Jointly Explain Variance",
      "scenario_id": "VAR-004_MULTIPLE_EVENT_EXPLANATION",
      "case_id": "CASE-004",
      "settlement_id": "setl_scen_004_9821",
      "variance_display": "-\u20b91,000.00",
      "core_lesson": "A \u20b9700 refund and a \u20b9300 adjustment individually cannot resolve the \u20b91,000 variance. Jointly, their verified sum satisfies the monetary constraint exactly.",
      "workflow_step": "Dual Causal Branches (\u20b9700 + \u20b9300) Combined at Monetary Adder Node",
      "badge_color": "violet"
    },
    {
      "demo_id": "demo_4",
      "title": "Demo 4: Honest Escalation",
      "subtitle": "Plausible \u2260 Proven (System Knows When It Doesn't Know)",
      "scenario_id": "VAR-008_WRONG_DATE_DECOY",
      "case_id": "CASE-008",
      "settlement_id": "setl_scen_008_1204",
      "variance_display": "-\u20b9500.00",
      "core_lesson": "A plausible-looking refund exists with matching amount, but its timestamp falls outside the cut-off window. The verifier rejects closure and safely escalates to human review.",
      "workflow_step": "Temporal Cut-off Violation \u2192 Safe Human Review Escalation (0% False Closure)",
      "badge_color": "rose"
    }
  ],
  "scenarios": [
    {
      "scenario_id": "VAR-001_REFUND_VARIANCE",
      "case_id": "CASE-001",
      "settlement_id": "setl_scen_001_9984",
      "category": "Settlement RCA",
      "expected_outcome": "RESOLVED",
      "expected_amount_inr": 2882.0,
      "actual_bank_credit_inr": 882.0,
      "variance_inr": -2000.0,
      "variance_paise": -200000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L5",
      "evidence_nodes": [
        {
          "evidence_id": "E-001",
          "entity_type": "REFUND",
          "entity_key": "ref_scen_001_9984",
          "amount_inr": -100.0,
          "relationship_path": "Refund ref_scen_001_9984 \u2192 Payment pay_scen_001_9984 \u2192 Settlement setl_scen_001_9984",
          "source_file": "refunds.csv",
          "sheet": "Refunds_FY25",
          "row": 10,
          "cell": "F10",
          "record_hash": "81ab6c0902f2ec0108e74e4841a963c1e390c3de05b724dbd3ba6a4c6672bf00",
          "evidence_level": "L5",
          "status": "VERIFIED",
          "role": "PRIMARY_CAUSE",
          "description": "Customer refund processed and deducted from payout balance"
        }
      ],
      "rejected_decoys": [],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Sum of verified deductions equals variance (-\u20b9100.00 = -\u20b9100.00)",
          "status": "PASS",
          "rule": "exact_amount_match"
        },
        {
          "name": "Settlement Membership",
          "description": "Refund is linked to payment in settlement setl_scen_001_9984",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "Refund processed within 48h settlement batch cut-off",
          "status": "PASS",
          "rule": "delta_t_within_bounds"
        },
        {
          "name": "State Validity",
          "description": "Refund state is SUCCESS (not failed/reversed)",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "L5 cryptographic trace to raw refunds.csv row",
          "status": "PASS",
          "rule": "cryptographic_hash_verified"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b92000.00 in settlement setl_scen_001_9984 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_001_9984')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=-200000)"
        ],
        "ai_confidence": "HIGH (0.94)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "APPROVED",
        "constraints_passed": 5,
        "constraints_total": 5,
        "final_decision": "RESOLVED",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": null
    },
    {
      "scenario_id": "VAR-002_SAME_AMOUNT_DECOY",
      "case_id": "CASE-002",
      "settlement_id": "setl_scen_002_8398",
      "category": "Settlement RCA",
      "expected_outcome": "RESOLVED",
      "expected_amount_inr": 5311.2,
      "actual_bank_credit_inr": 2811.2,
      "variance_inr": -2500.0,
      "variance_paise": -250000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L5",
      "evidence_nodes": [
        {
          "evidence_id": "E-002A",
          "entity_type": "REFUND",
          "entity_key": "ref_scen_002_valid",
          "amount_inr": -150.0,
          "relationship_path": "Refund ref_scen_002_valid \u2192 Payment pay_scen_002_valid \u2192 Settlement setl_scen_002_8398",
          "source_file": "refunds.csv",
          "sheet": "Refunds_FY25",
          "row": 13,
          "cell": "F13",
          "record_hash": "9bb8cbb10d8f567db30e6f4e27726b2acf7530033841d4c6a885b0128857b425",
          "evidence_level": "L5",
          "status": "VERIFIED",
          "role": "PRIMARY_CAUSE",
          "description": "Valid refund attached to settlement order"
        }
      ],
      "rejected_decoys": [
        {
          "evidence_id": "E-002B",
          "entity_type": "REFUND",
          "entity_key": "ref_scen_002_decoy",
          "amount_inr": -150.0,
          "relationship_path": "Refund ref_scen_002_decoy \u2192 Payment pay_other_999 \u2192 Settlement setl_external_888",
          "source_file": "refunds.csv",
          "sheet": "Refunds_FY25",
          "row": 14,
          "cell": "F14",
          "record_hash": "0214fbd7992e0a2f7be404d982951e4d73f0905c65726e7d61f5075466c9e657",
          "evidence_level": "L1",
          "status": "REJECTED",
          "rejection_reason": "Foreign key mismatch: Payment belongs to setl_external_888, NOT current settlement",
          "lesson": "Amount match alone (\u20b9150.00) is insufficient without verified relational provenance."
        }
      ],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Single verified refund matches -\u20b9150.00 variance",
          "status": "PASS",
          "rule": "exact_amount_match"
        },
        {
          "name": "Settlement Membership",
          "description": "Valid refund verified; decoy rejected due to unlinked payment",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "Valid refund timestamp verified",
          "status": "PASS",
          "rule": "delta_t_within_bounds"
        },
        {
          "name": "State Validity",
          "description": "Terminal status verified",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Unbroken provenance chain for E-002A",
          "status": "PASS",
          "rule": "cryptographic_hash_verified"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b92500.00 in settlement setl_scen_002_8398 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_002_8398')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=-250000)"
        ],
        "ai_confidence": "HIGH (0.94)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "APPROVED",
        "constraints_passed": 5,
        "constraints_total": 5,
        "final_decision": "RESOLVED",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": null
    },
    {
      "scenario_id": "VAR-003_PARTIAL_EXPLANATION",
      "case_id": "CASE-003",
      "settlement_id": "setl_scen_003_7992",
      "category": "Settlement RCA",
      "expected_outcome": "PARTIALLY_RESOLVED",
      "expected_amount_inr": 4764.0,
      "actual_bank_credit_inr": -236.0,
      "variance_inr": -5000.0,
      "variance_paise": -500000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L2",
      "evidence_nodes": [
        {
          "evidence_id": "E-003",
          "entity_type": "VARIANCE",
          "entity_key": "evt_var-003_partial_explanation",
          "amount_inr": -5000.0,
          "relationship_path": "UNEXPLAINED \u2192 Settlement setl_scen_003_7992",
          "source_file": "settlements.csv",
          "sheet": "Settlement_Recon",
          "row": 16,
          "cell": "D16",
          "record_hash": "2f9373cc189683dc485d8fb5ddc244b385b3f536c92f6ff5ff3e59866f76c921",
          "evidence_level": "L2",
          "status": "UNRESOLVED",
          "role": "UNRESOLVED_DISCREPANCY",
          "description": "Unexplained financial variance requiring human operational audit"
        }
      ],
      "rejected_decoys": [],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Target variance \u20b95000.00",
          "status": "FAIL",
          "rule": "monetary_verification"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked to setl_scen_003_7992",
          "status": "WARN",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "Cut-off timestamp verification",
          "status": "FAIL",
          "rule": "temporal_horizon"
        },
        {
          "name": "State Validity",
          "description": "Terminal status verification",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Cryptographic file provenance",
          "status": "FAIL",
          "rule": "hash_verified"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b95000.00 in settlement setl_scen_003_7992 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_003_7992')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=-500000)"
        ],
        "ai_confidence": "HIGH (0.94)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "PARTIAL_MATCH",
        "constraints_passed": 1,
        "constraints_total": 5,
        "final_decision": "PARTIALLY_RESOLVED",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": null
    },
    {
      "scenario_id": "VAR-004_MULTIPLE_EVENT_EXPLANATION",
      "case_id": "CASE-004",
      "settlement_id": "setl_scen_004_2582",
      "category": "Settlement RCA",
      "expected_outcome": "RESOLVED",
      "expected_amount_inr": 13646.0,
      "actual_bank_credit_inr": 12646.0,
      "variance_inr": -1000.0,
      "variance_paise": -100000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L5",
      "evidence_nodes": [
        {
          "evidence_id": "E-004A",
          "entity_type": "REFUND",
          "entity_key": "ref_scen_004_partA",
          "amount_inr": -700.0,
          "relationship_path": "Refund ref_scen_004_partA \u2192 Payment pay_scen_004_A \u2192 Settlement setl_scen_004_2582",
          "source_file": "refunds.csv",
          "sheet": "Refunds_FY25",
          "row": 19,
          "cell": "F19",
          "record_hash": "e1058da7e864bb9fc6970602ed6c41bd6679154df4a17c6374352c438e757d20",
          "evidence_level": "L5",
          "status": "VERIFIED",
          "role": "PARTIAL_CAUSE",
          "description": "Partial refund on high-value order (\u20b9700.00)"
        },
        {
          "evidence_id": "E-004B",
          "entity_type": "ADJUSTMENT",
          "entity_key": "adj_scen_004_partB",
          "amount_inr": -300.0,
          "relationship_path": "Adjustment adj_scen_004_partB \u2192 Settlement setl_scen_004_2582",
          "source_file": "adjustments.csv",
          "sheet": "Fee_Adjustments",
          "row": 21,
          "cell": "D21",
          "record_hash": "1921954ede3a555af11f0b00674169c9d60147350c2687fb6bf0e03482edb818",
          "evidence_level": "L5",
          "status": "VERIFIED",
          "role": "PARTIAL_CAUSE",
          "description": "Gateway MDR fee reconciliation adjustment (\u20b9300.00)"
        }
      ],
      "rejected_decoys": [],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Joint sum: \u20b9700.00 + \u20b9300.00 = \u20b91,000.00 (exact match)",
          "status": "PASS",
          "rule": "sum_events_equals_variance"
        },
        {
          "name": "Settlement Membership",
          "description": "Both refund and adjustment verified against settlement ID",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "Both events occurred within the T+2 settlement window",
          "status": "PASS",
          "rule": "delta_t_within_bounds"
        },
        {
          "name": "State Validity",
          "description": "Both transactions confirmed terminal success",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Dual L5 provenance verified across refunds.csv and adjustments.csv",
          "status": "PASS",
          "rule": "cryptographic_hash_verified"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b91000.00 in settlement setl_scen_004_2582 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_004_2582')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=-100000)"
        ],
        "ai_confidence": "HIGH (0.94)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "APPROVED",
        "constraints_passed": 5,
        "constraints_total": 5,
        "final_decision": "RESOLVED",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": null
    },
    {
      "scenario_id": "VAR-005_UPI_LATE_SUCCESS",
      "case_id": "CASE-005",
      "settlement_id": "setl_scen_005_6761",
      "category": "UPI State Investigation",
      "expected_outcome": "RESOLVED",
      "expected_amount_inr": 3417.4,
      "actual_bank_credit_inr": 3417.4,
      "variance_inr": 0.0,
      "variance_paise": 0,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L5",
      "evidence_nodes": [
        {
          "evidence_id": "E-005",
          "entity_type": "VARIANCE",
          "entity_key": "evt_var-005_upi_late_success",
          "amount_inr": 0.0,
          "relationship_path": "UNEXPLAINED \u2192 Settlement setl_scen_005_6761",
          "source_file": "settlements.csv",
          "sheet": "Settlement_Recon",
          "row": 22,
          "cell": "D22",
          "record_hash": "838b52d0e43b77a3a50a59c77342c9eafe52a8378852d08fb5ac1c1699143776",
          "evidence_level": "L5",
          "status": "VERIFIED",
          "role": "PRIMARY_CAUSE",
          "description": "Verified causal transaction for VAR-005_UPI_LATE_SUCCESS"
        }
      ],
      "rejected_decoys": [],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Target variance \u20b90.00",
          "status": "PASS",
          "rule": "monetary_verification"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked to setl_scen_005_6761",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "Cut-off timestamp verification",
          "status": "PASS",
          "rule": "temporal_horizon"
        },
        {
          "name": "State Validity",
          "description": "Terminal status verification",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Cryptographic file provenance",
          "status": "PASS",
          "rule": "hash_verified"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b90.00 in settlement setl_scen_005_6761 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_005_6761')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=0)"
        ],
        "ai_confidence": "HIGH (0.94)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "APPROVED",
        "constraints_passed": 5,
        "constraints_total": 5,
        "final_decision": "RESOLVED",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": null
    },
    {
      "scenario_id": "VAR-006_UPI_DEBIT_REVERSAL",
      "case_id": "CASE-006",
      "settlement_id": "N/A",
      "category": "UPI State Investigation",
      "expected_outcome": "RESOLVED",
      "expected_amount_inr": 10000.0,
      "actual_bank_credit_inr": 10000.0,
      "variance_inr": 0.0,
      "variance_paise": 0,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L5",
      "evidence_nodes": [
        {
          "evidence_id": "E-006",
          "entity_type": "VARIANCE",
          "entity_key": "evt_var-006_upi_debit_reversal",
          "amount_inr": 0.0,
          "relationship_path": "UNEXPLAINED \u2192 Settlement N/A",
          "source_file": "settlements.csv",
          "sheet": "Settlement_Recon",
          "row": 25,
          "cell": "D25",
          "record_hash": "04da28c29cf8700a0d444e2b813767f4e53595428a22b099a50f23d2f15b8e6a",
          "evidence_level": "L5",
          "status": "VERIFIED",
          "role": "PRIMARY_CAUSE",
          "description": "Verified causal transaction for VAR-006_UPI_DEBIT_REVERSAL"
        }
      ],
      "rejected_decoys": [],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Target variance \u20b90.00",
          "status": "PASS",
          "rule": "monetary_verification"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked to N/A",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "Cut-off timestamp verification",
          "status": "PASS",
          "rule": "temporal_horizon"
        },
        {
          "name": "State Validity",
          "description": "Terminal status verification",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Cryptographic file provenance",
          "status": "PASS",
          "rule": "hash_verified"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b90.00 in settlement N/A is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('N/A')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=0)"
        ],
        "ai_confidence": "HIGH (0.94)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "APPROVED",
        "constraints_passed": 5,
        "constraints_total": 5,
        "final_decision": "RESOLVED",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": null
    },
    {
      "scenario_id": "VAR-007_DELAYED_BANK_CREDIT",
      "case_id": "CASE-007",
      "settlement_id": "setl_scen_007_3955",
      "category": "Bank Settlement State",
      "expected_outcome": "VALID_DELAYED_CREDIT",
      "expected_amount_inr": 19528.0,
      "actual_bank_credit_inr": 19528.0,
      "variance_inr": 0.0,
      "variance_paise": 0,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L5",
      "evidence_nodes": [
        {
          "evidence_id": "E-007",
          "entity_type": "VARIANCE",
          "entity_key": "evt_var-007_delayed_bank_credit",
          "amount_inr": 0.0,
          "relationship_path": "UNEXPLAINED \u2192 Settlement setl_scen_007_3955",
          "source_file": "settlements.csv",
          "sheet": "Settlement_Recon",
          "row": 28,
          "cell": "D28",
          "record_hash": "b3547a655ca7783265f68255c81a119a17cbf31f79d95d338f6bc49b5ee55ca1",
          "evidence_level": "L5",
          "status": "VERIFIED",
          "role": "PRIMARY_CAUSE",
          "description": "Verified causal transaction for VAR-007_DELAYED_BANK_CREDIT"
        }
      ],
      "rejected_decoys": [],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Target variance \u20b90.00",
          "status": "PASS",
          "rule": "monetary_verification"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked to setl_scen_007_3955",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "Cut-off timestamp verification",
          "status": "PASS",
          "rule": "temporal_horizon"
        },
        {
          "name": "State Validity",
          "description": "Terminal status verification",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Cryptographic file provenance",
          "status": "PASS",
          "rule": "hash_verified"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b90.00 in settlement setl_scen_007_3955 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_007_3955')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=0)"
        ],
        "ai_confidence": "HIGH (0.94)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "APPROVED",
        "constraints_passed": 5,
        "constraints_total": 5,
        "final_decision": "VALID_DELAYED_CREDIT",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": null
    },
    {
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
      "evidence_level": "L2",
      "evidence_nodes": [],
      "rejected_decoys": [
        {
          "evidence_id": "E-008_DECOY",
          "entity_type": "REFUND",
          "entity_key": "ref_scen_008_outdated",
          "amount_inr": 4000.0,
          "relationship_path": "Refund ref_scen_008_outdated \u2192 Payment pay_old_301 \u2192 Settlement setl_scen_008_2140",
          "source_file": "refunds.csv",
          "sheet": "Refunds_FY24_Archive",
          "row": 31,
          "cell": "F31",
          "record_hash": "a601b489d93d3511c5d11be95731c96e2415b311830f6e54186021447399bce6",
          "evidence_level": "L2",
          "status": "REJECTED",
          "rejection_reason": "Temporal Cut-off Violation: Refund timestamp is 14 days prior to settlement batch cut-off",
          "lesson": "Plausible \u2260 Proven. System rejects out-of-window decoys and safely escalates."
        }
      ],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Candidate event matched variance amount",
          "status": "PASS",
          "rule": "amount_heuristic"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked payment found in historic index",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "VIOLATION: Event occurred 14 days prior (limit: 48h)",
          "status": "FAIL",
          "rule": "temporal_horizon_exceeded"
        },
        {
          "name": "State Validity",
          "description": "State verified",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Source file belongs to archived FY24 batch",
          "status": "FAIL",
          "rule": "stale_provenance"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b94000.00 in settlement setl_scen_008_2140 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_008_2140')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=400000)"
        ],
        "ai_confidence": "LOW (0.31)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "REJECTED",
        "constraints_passed": 3,
        "constraints_total": 5,
        "final_decision": "ESCALATE",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": {
        "escalation_reason": "No valid causal evidence chain satisfies all 5 deterministic financial constraints.",
        "rejection_summary": [
          "\u2717 Monetary explanation incomplete or missing",
          "\u2717 Unverified settlement foreign key relationship",
          "\u2717 Decoy transactions rejected by temporal bounds check"
        ],
        "recommended_action": "Route to Tier-2 Financial Operations Audit Queue.",
        "safety_guarantee": "System safely escalated rather than falsely closing financial variance (0% false closure invariant)."
      }
    },
    {
      "scenario_id": "VAR-009_WRONG_PAYMENT_DECOY",
      "case_id": "CASE-009",
      "settlement_id": "setl_scen_009_6585",
      "category": "Settlement RCA",
      "expected_outcome": "ESCALATE",
      "expected_amount_inr": 5287.6,
      "actual_bank_credit_inr": 8787.6,
      "variance_inr": 3500.0,
      "variance_paise": 350000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L2",
      "evidence_nodes": [],
      "rejected_decoys": [
        {
          "evidence_id": "E-008_DECOY",
          "entity_type": "REFUND",
          "entity_key": "ref_scen_008_outdated",
          "amount_inr": 3500.0,
          "relationship_path": "Refund ref_scen_008_outdated \u2192 Payment pay_old_301 \u2192 Settlement setl_scen_009_6585",
          "source_file": "refunds.csv",
          "sheet": "Refunds_FY24_Archive",
          "row": 34,
          "cell": "F34",
          "record_hash": "5d8854a8df769f837dbfa366835fedcd682201100602c9b911ceae9cc31f5826",
          "evidence_level": "L2",
          "status": "REJECTED",
          "rejection_reason": "Temporal Cut-off Violation: Refund timestamp is 14 days prior to settlement batch cut-off",
          "lesson": "Plausible \u2260 Proven. System rejects out-of-window decoys and safely escalates."
        }
      ],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Candidate event matched variance amount",
          "status": "PASS",
          "rule": "amount_heuristic"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked payment found in historic index",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "VIOLATION: Event occurred 14 days prior (limit: 48h)",
          "status": "FAIL",
          "rule": "temporal_horizon_exceeded"
        },
        {
          "name": "State Validity",
          "description": "State verified",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Source file belongs to archived FY24 batch",
          "status": "FAIL",
          "rule": "stale_provenance"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b93500.00 in settlement setl_scen_009_6585 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_009_6585')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=350000)"
        ],
        "ai_confidence": "LOW (0.31)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "REJECTED",
        "constraints_passed": 3,
        "constraints_total": 5,
        "final_decision": "ESCALATE",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": {
        "escalation_reason": "No valid causal evidence chain satisfies all 5 deterministic financial constraints.",
        "rejection_summary": [
          "\u2717 Monetary explanation incomplete or missing",
          "\u2717 Unverified settlement foreign key relationship",
          "\u2717 Decoy transactions rejected by temporal bounds check"
        ],
        "recommended_action": "Route to Tier-2 Financial Operations Audit Queue.",
        "safety_guarantee": "System safely escalated rather than falsely closing financial variance (0% false closure invariant)."
      }
    },
    {
      "scenario_id": "VAR-010_COMPLETELY_UNEXPLAINED",
      "case_id": "CASE-010",
      "settlement_id": "setl_scen_010_1815",
      "category": "Settlement RCA",
      "expected_outcome": "ESCALATE",
      "expected_amount_inr": 14292.0,
      "actual_bank_credit_inr": 29292.0,
      "variance_inr": 15000.0,
      "variance_paise": 1500000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L2",
      "evidence_nodes": [],
      "rejected_decoys": [
        {
          "evidence_id": "E-008_DECOY",
          "entity_type": "REFUND",
          "entity_key": "ref_scen_008_outdated",
          "amount_inr": 15000.0,
          "relationship_path": "Refund ref_scen_008_outdated \u2192 Payment pay_old_301 \u2192 Settlement setl_scen_010_1815",
          "source_file": "refunds.csv",
          "sheet": "Refunds_FY24_Archive",
          "row": 37,
          "cell": "F37",
          "record_hash": "2bb516f3b88fcfae0c24b428165060789484d6c4b21ad4e0e3f8f7623b12914f",
          "evidence_level": "L2",
          "status": "REJECTED",
          "rejection_reason": "Temporal Cut-off Violation: Refund timestamp is 14 days prior to settlement batch cut-off",
          "lesson": "Plausible \u2260 Proven. System rejects out-of-window decoys and safely escalates."
        }
      ],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Candidate event matched variance amount",
          "status": "PASS",
          "rule": "amount_heuristic"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked payment found in historic index",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "VIOLATION: Event occurred 14 days prior (limit: 48h)",
          "status": "FAIL",
          "rule": "temporal_horizon_exceeded"
        },
        {
          "name": "State Validity",
          "description": "State verified",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Source file belongs to archived FY24 batch",
          "status": "FAIL",
          "rule": "stale_provenance"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b915000.00 in settlement setl_scen_010_1815 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_010_1815')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=1500000)"
        ],
        "ai_confidence": "LOW (0.31)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "REJECTED",
        "constraints_passed": 3,
        "constraints_total": 5,
        "final_decision": "ESCALATE",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": {
        "escalation_reason": "No valid causal evidence chain satisfies all 5 deterministic financial constraints.",
        "rejection_summary": [
          "\u2717 Monetary explanation incomplete or missing",
          "\u2717 Unverified settlement foreign key relationship",
          "\u2717 Decoy transactions rejected by temporal bounds check"
        ],
        "recommended_action": "Route to Tier-2 Financial Operations Audit Queue.",
        "safety_guarantee": "System safely escalated rather than falsely closing financial variance (0% false closure invariant)."
      }
    },
    {
      "scenario_id": "AG-001_MISSING_MEMBERSHIP",
      "case_id": "CASE-AG-001",
      "settlement_id": "setl_scen_004_2582",
      "category": "Agentic Investigation",
      "expected_outcome": "RESOLVED",
      "expected_amount_inr": 13646.0,
      "actual_bank_credit_inr": 12646.0,
      "variance_inr": -1000.0,
      "variance_paise": -100000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L5",
      "evidence_nodes": [
        {
          "evidence_id": "E-011",
          "entity_type": "VARIANCE",
          "entity_key": "evt_ag-001_missing_membership",
          "amount_inr": -1000.0,
          "relationship_path": "UNEXPLAINED \u2192 Settlement setl_scen_004_2582",
          "source_file": "settlements.csv",
          "sheet": "Settlement_Recon",
          "row": 40,
          "cell": "D40",
          "record_hash": "722e19e97eb6c7248b26b3dbe368b0c14756b7027fcaa46a6798dc907eeee4f1",
          "evidence_level": "L5",
          "status": "VERIFIED",
          "role": "PRIMARY_CAUSE",
          "description": "Verified causal transaction for AG-001_MISSING_MEMBERSHIP"
        }
      ],
      "rejected_decoys": [],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Target variance \u20b91000.00",
          "status": "PASS",
          "rule": "monetary_verification"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked to setl_scen_004_2582",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "Cut-off timestamp verification",
          "status": "PASS",
          "rule": "temporal_horizon"
        },
        {
          "name": "State Validity",
          "description": "Terminal status verification",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Cryptographic file provenance",
          "status": "PASS",
          "rule": "hash_verified"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b91000.00 in settlement setl_scen_004_2582 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_004_2582')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=-100000)"
        ],
        "ai_confidence": "HIGH (0.94)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "APPROVED",
        "constraints_passed": 5,
        "constraints_total": 5,
        "final_decision": "RESOLVED",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": null
    },
    {
      "scenario_id": "AG-002_WRONG_MEMBERSHIP",
      "case_id": "CASE-AG-002",
      "settlement_id": "setl_scen_002_8398",
      "category": "Agentic Investigation",
      "expected_outcome": "ESCALATE",
      "expected_amount_inr": 5311.2,
      "actual_bank_credit_inr": 2811.2,
      "variance_inr": -2500.0,
      "variance_paise": -250000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L2",
      "evidence_nodes": [],
      "rejected_decoys": [
        {
          "evidence_id": "E-008_DECOY",
          "entity_type": "REFUND",
          "entity_key": "ref_scen_008_outdated",
          "amount_inr": -2500.0,
          "relationship_path": "Refund ref_scen_008_outdated \u2192 Payment pay_old_301 \u2192 Settlement setl_scen_002_8398",
          "source_file": "refunds.csv",
          "sheet": "Refunds_FY24_Archive",
          "row": 43,
          "cell": "F43",
          "record_hash": "0e3d0445b179f94af9a4447f499321d9525e10ce18628642dcedce7d5fbeb129",
          "evidence_level": "L2",
          "status": "REJECTED",
          "rejection_reason": "Temporal Cut-off Violation: Refund timestamp is 14 days prior to settlement batch cut-off",
          "lesson": "Plausible \u2260 Proven. System rejects out-of-window decoys and safely escalates."
        }
      ],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Candidate event matched variance amount",
          "status": "PASS",
          "rule": "amount_heuristic"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked payment found in historic index",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "VIOLATION: Event occurred 14 days prior (limit: 48h)",
          "status": "FAIL",
          "rule": "temporal_horizon_exceeded"
        },
        {
          "name": "State Validity",
          "description": "State verified",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Source file belongs to archived FY24 batch",
          "status": "FAIL",
          "rule": "stale_provenance"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b92500.00 in settlement setl_scen_002_8398 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_002_8398')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=-250000)"
        ],
        "ai_confidence": "LOW (0.31)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "REJECTED",
        "constraints_passed": 3,
        "constraints_total": 5,
        "final_decision": "ESCALATE",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": {
        "escalation_reason": "No valid causal evidence chain satisfies all 5 deterministic financial constraints.",
        "rejection_summary": [
          "\u2717 Monetary explanation incomplete or missing",
          "\u2717 Unverified settlement foreign key relationship",
          "\u2717 Decoy transactions rejected by temporal bounds check"
        ],
        "recommended_action": "Route to Tier-2 Financial Operations Audit Queue.",
        "safety_guarantee": "System safely escalated rather than falsely closing financial variance (0% false closure invariant)."
      }
    },
    {
      "scenario_id": "AG-003_MISSING_UPI_HISTORY",
      "case_id": "CASE-AG-003",
      "settlement_id": "N/A",
      "category": "Agentic Investigation",
      "expected_outcome": "RESOLVED",
      "expected_amount_inr": 10000.0,
      "actual_bank_credit_inr": 10000.0,
      "variance_inr": 0.0,
      "variance_paise": 0,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L5",
      "evidence_nodes": [
        {
          "evidence_id": "E-013",
          "entity_type": "VARIANCE",
          "entity_key": "evt_ag-003_missing_upi_history",
          "amount_inr": 0.0,
          "relationship_path": "UNEXPLAINED \u2192 Settlement N/A",
          "source_file": "settlements.csv",
          "sheet": "Settlement_Recon",
          "row": 46,
          "cell": "D46",
          "record_hash": "fd0a8e0a615288e237f2f4e0a30af43985540292224849b37e026261adac3d77",
          "evidence_level": "L5",
          "status": "VERIFIED",
          "role": "PRIMARY_CAUSE",
          "description": "Verified causal transaction for AG-003_MISSING_UPI_HISTORY"
        }
      ],
      "rejected_decoys": [],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Target variance \u20b90.00",
          "status": "PASS",
          "rule": "monetary_verification"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked to N/A",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "Cut-off timestamp verification",
          "status": "PASS",
          "rule": "temporal_horizon"
        },
        {
          "name": "State Validity",
          "description": "Terminal status verification",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Cryptographic file provenance",
          "status": "PASS",
          "rule": "hash_verified"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b90.00 in settlement N/A is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('N/A')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=0)"
        ],
        "ai_confidence": "HIGH (0.94)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "APPROVED",
        "constraints_passed": 5,
        "constraints_total": 5,
        "final_decision": "RESOLVED",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": null
    },
    {
      "scenario_id": "AG-004_LATE_UPI_SUCCESS",
      "case_id": "CASE-AG-004",
      "settlement_id": "setl_scen_005_6761",
      "category": "Agentic Investigation",
      "expected_outcome": "RESOLVED",
      "expected_amount_inr": 3417.4,
      "actual_bank_credit_inr": 3417.4,
      "variance_inr": 0.0,
      "variance_paise": 0,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L5",
      "evidence_nodes": [
        {
          "evidence_id": "E-014",
          "entity_type": "VARIANCE",
          "entity_key": "evt_ag-004_late_upi_success",
          "amount_inr": 0.0,
          "relationship_path": "UNEXPLAINED \u2192 Settlement setl_scen_005_6761",
          "source_file": "settlements.csv",
          "sheet": "Settlement_Recon",
          "row": 49,
          "cell": "D49",
          "record_hash": "e6a33757cc26482ebf6b9aecbf9ed1cb80fefa24887c8e9be23908cfe526dc4c",
          "evidence_level": "L5",
          "status": "VERIFIED",
          "role": "PRIMARY_CAUSE",
          "description": "Verified causal transaction for AG-004_LATE_UPI_SUCCESS"
        }
      ],
      "rejected_decoys": [],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Target variance \u20b90.00",
          "status": "PASS",
          "rule": "monetary_verification"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked to setl_scen_005_6761",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "Cut-off timestamp verification",
          "status": "PASS",
          "rule": "temporal_horizon"
        },
        {
          "name": "State Validity",
          "description": "Terminal status verification",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Cryptographic file provenance",
          "status": "PASS",
          "rule": "hash_verified"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b90.00 in settlement setl_scen_005_6761 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_005_6761')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=0)"
        ],
        "ai_confidence": "HIGH (0.94)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "APPROVED",
        "constraints_passed": 5,
        "constraints_total": 5,
        "final_decision": "RESOLVED",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": null
    },
    {
      "scenario_id": "AG-005_CONFLICTING_REFUND",
      "case_id": "CASE-AG-005",
      "settlement_id": "setl_scen_002_8398",
      "category": "Agentic Investigation",
      "expected_outcome": "ESCALATE",
      "expected_amount_inr": 5311.2,
      "actual_bank_credit_inr": 2811.2,
      "variance_inr": -2500.0,
      "variance_paise": -250000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L2",
      "evidence_nodes": [],
      "rejected_decoys": [
        {
          "evidence_id": "E-008_DECOY",
          "entity_type": "REFUND",
          "entity_key": "ref_scen_008_outdated",
          "amount_inr": -2500.0,
          "relationship_path": "Refund ref_scen_008_outdated \u2192 Payment pay_old_301 \u2192 Settlement setl_scen_002_8398",
          "source_file": "refunds.csv",
          "sheet": "Refunds_FY24_Archive",
          "row": 52,
          "cell": "F52",
          "record_hash": "0e3d0445b179f94af9a4447f499321d9525e10ce18628642dcedce7d5fbeb129",
          "evidence_level": "L2",
          "status": "REJECTED",
          "rejection_reason": "Temporal Cut-off Violation: Refund timestamp is 14 days prior to settlement batch cut-off",
          "lesson": "Plausible \u2260 Proven. System rejects out-of-window decoys and safely escalates."
        }
      ],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Candidate event matched variance amount",
          "status": "PASS",
          "rule": "amount_heuristic"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked payment found in historic index",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "VIOLATION: Event occurred 14 days prior (limit: 48h)",
          "status": "FAIL",
          "rule": "temporal_horizon_exceeded"
        },
        {
          "name": "State Validity",
          "description": "State verified",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Source file belongs to archived FY24 batch",
          "status": "FAIL",
          "rule": "stale_provenance"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b92500.00 in settlement setl_scen_002_8398 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_002_8398')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=-250000)"
        ],
        "ai_confidence": "LOW (0.31)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "REJECTED",
        "constraints_passed": 3,
        "constraints_total": 5,
        "final_decision": "ESCALATE",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": {
        "escalation_reason": "No valid causal evidence chain satisfies all 5 deterministic financial constraints.",
        "rejection_summary": [
          "\u2717 Monetary explanation incomplete or missing",
          "\u2717 Unverified settlement foreign key relationship",
          "\u2717 Decoy transactions rejected by temporal bounds check"
        ],
        "recommended_action": "Route to Tier-2 Financial Operations Audit Queue.",
        "safety_guarantee": "System safely escalated rather than falsely closing financial variance (0% false closure invariant)."
      }
    },
    {
      "scenario_id": "AG-006_TRULY_UNEXPLAINED",
      "case_id": "CASE-AG-006",
      "settlement_id": "setl_scen_010_1815",
      "category": "Agentic Investigation",
      "expected_outcome": "ESCALATE",
      "expected_amount_inr": 14292.0,
      "actual_bank_credit_inr": -708.0,
      "variance_inr": -15000.0,
      "variance_paise": -1500000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L2",
      "evidence_nodes": [],
      "rejected_decoys": [
        {
          "evidence_id": "E-008_DECOY",
          "entity_type": "REFUND",
          "entity_key": "ref_scen_008_outdated",
          "amount_inr": -15000.0,
          "relationship_path": "Refund ref_scen_008_outdated \u2192 Payment pay_old_301 \u2192 Settlement setl_scen_010_1815",
          "source_file": "refunds.csv",
          "sheet": "Refunds_FY24_Archive",
          "row": 55,
          "cell": "F55",
          "record_hash": "2bb516f3b88fcfae0c24b428165060789484d6c4b21ad4e0e3f8f7623b12914f",
          "evidence_level": "L2",
          "status": "REJECTED",
          "rejection_reason": "Temporal Cut-off Violation: Refund timestamp is 14 days prior to settlement batch cut-off",
          "lesson": "Plausible \u2260 Proven. System rejects out-of-window decoys and safely escalates."
        }
      ],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Candidate event matched variance amount",
          "status": "PASS",
          "rule": "amount_heuristic"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked payment found in historic index",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "VIOLATION: Event occurred 14 days prior (limit: 48h)",
          "status": "FAIL",
          "rule": "temporal_horizon_exceeded"
        },
        {
          "name": "State Validity",
          "description": "State verified",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Source file belongs to archived FY24 batch",
          "status": "FAIL",
          "rule": "stale_provenance"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b915000.00 in settlement setl_scen_010_1815 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_010_1815')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=-1500000)"
        ],
        "ai_confidence": "LOW (0.31)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "REJECTED",
        "constraints_passed": 3,
        "constraints_total": 5,
        "final_decision": "ESCALATE",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": {
        "escalation_reason": "No valid causal evidence chain satisfies all 5 deterministic financial constraints.",
        "rejection_summary": [
          "\u2717 Monetary explanation incomplete or missing",
          "\u2717 Unverified settlement foreign key relationship",
          "\u2717 Decoy transactions rejected by temporal bounds check"
        ],
        "recommended_action": "Route to Tier-2 Financial Operations Audit Queue.",
        "safety_guarantee": "System safely escalated rather than falsely closing financial variance (0% false closure invariant)."
      }
    },
    {
      "scenario_id": "AG-007_DECOY_EXPLOSION",
      "case_id": "CASE-AG-007",
      "settlement_id": "setl_scen_002_8398",
      "category": "Agentic Investigation",
      "expected_outcome": "RESOLVED",
      "expected_amount_inr": 5311.2,
      "actual_bank_credit_inr": 2811.2,
      "variance_inr": -2500.0,
      "variance_paise": -250000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L5",
      "evidence_nodes": [
        {
          "evidence_id": "E-017",
          "entity_type": "VARIANCE",
          "entity_key": "evt_ag-007_decoy_explosion",
          "amount_inr": -2500.0,
          "relationship_path": "UNEXPLAINED \u2192 Settlement setl_scen_002_8398",
          "source_file": "settlements.csv",
          "sheet": "Settlement_Recon",
          "row": 58,
          "cell": "D58",
          "record_hash": "2ad388d922ed03cb4e4d37c5b3dc44c55d3fff1b2684c75bc4e5b3adf753bd1a",
          "evidence_level": "L5",
          "status": "VERIFIED",
          "role": "PRIMARY_CAUSE",
          "description": "Verified causal transaction for AG-007_DECOY_EXPLOSION"
        }
      ],
      "rejected_decoys": [],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Target variance \u20b92500.00",
          "status": "PASS",
          "rule": "monetary_verification"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked to setl_scen_002_8398",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "Cut-off timestamp verification",
          "status": "PASS",
          "rule": "temporal_horizon"
        },
        {
          "name": "State Validity",
          "description": "Terminal status verification",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Cryptographic file provenance",
          "status": "PASS",
          "rule": "hash_verified"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b92500.00 in settlement setl_scen_002_8398 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_002_8398')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=-250000)"
        ],
        "ai_confidence": "HIGH (0.94)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "APPROVED",
        "constraints_passed": 5,
        "constraints_total": 5,
        "final_decision": "RESOLVED",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": null
    },
    {
      "scenario_id": "AG-008_MULTI_STEP_FLAGSHIP",
      "case_id": "CASE-AG-008",
      "settlement_id": "setl_scen_004_2582",
      "category": "Agentic Investigation",
      "expected_outcome": "RESOLVED",
      "expected_amount_inr": 13646.0,
      "actual_bank_credit_inr": 12646.0,
      "variance_inr": -1000.0,
      "variance_paise": -100000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L5",
      "evidence_nodes": [
        {
          "evidence_id": "E-018",
          "entity_type": "VARIANCE",
          "entity_key": "evt_ag-008_multi_step_flagship",
          "amount_inr": -1000.0,
          "relationship_path": "UNEXPLAINED \u2192 Settlement setl_scen_004_2582",
          "source_file": "settlements.csv",
          "sheet": "Settlement_Recon",
          "row": 61,
          "cell": "D61",
          "record_hash": "2371b8066c45d029574b3ba748ccf321d4b3501f28e750fdd1f0b0a0dd13efb1",
          "evidence_level": "L5",
          "status": "VERIFIED",
          "role": "PRIMARY_CAUSE",
          "description": "Verified causal transaction for AG-008_MULTI_STEP_FLAGSHIP"
        }
      ],
      "rejected_decoys": [],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Target variance \u20b91000.00",
          "status": "PASS",
          "rule": "monetary_verification"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked to setl_scen_004_2582",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "Cut-off timestamp verification",
          "status": "PASS",
          "rule": "temporal_horizon"
        },
        {
          "name": "State Validity",
          "description": "Terminal status verification",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Cryptographic file provenance",
          "status": "PASS",
          "rule": "hash_verified"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b91000.00 in settlement setl_scen_004_2582 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_004_2582')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=-100000)"
        ],
        "ai_confidence": "HIGH (0.94)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "APPROVED",
        "constraints_passed": 5,
        "constraints_total": 5,
        "final_decision": "RESOLVED",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": null
    },
    {
      "scenario_id": "AG-009_REDUNDANT_TOOL_LOOP",
      "case_id": "CASE-AG-009",
      "settlement_id": "setl_scen_004_2582",
      "category": "Agentic Investigation",
      "expected_outcome": "ESCALATE",
      "expected_amount_inr": 13646.0,
      "actual_bank_credit_inr": 12646.0,
      "variance_inr": -1000.0,
      "variance_paise": -100000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L2",
      "evidence_nodes": [],
      "rejected_decoys": [
        {
          "evidence_id": "E-008_DECOY",
          "entity_type": "REFUND",
          "entity_key": "ref_scen_008_outdated",
          "amount_inr": -1000.0,
          "relationship_path": "Refund ref_scen_008_outdated \u2192 Payment pay_old_301 \u2192 Settlement setl_scen_004_2582",
          "source_file": "refunds.csv",
          "sheet": "Refunds_FY24_Archive",
          "row": 64,
          "cell": "F64",
          "record_hash": "c3c66d558779d3b91047bf0fd9f069c0c04f232e9207639b155bba073d65885b",
          "evidence_level": "L2",
          "status": "REJECTED",
          "rejection_reason": "Temporal Cut-off Violation: Refund timestamp is 14 days prior to settlement batch cut-off",
          "lesson": "Plausible \u2260 Proven. System rejects out-of-window decoys and safely escalates."
        }
      ],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Candidate event matched variance amount",
          "status": "PASS",
          "rule": "amount_heuristic"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked payment found in historic index",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "VIOLATION: Event occurred 14 days prior (limit: 48h)",
          "status": "FAIL",
          "rule": "temporal_horizon_exceeded"
        },
        {
          "name": "State Validity",
          "description": "State verified",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Source file belongs to archived FY24 batch",
          "status": "FAIL",
          "rule": "stale_provenance"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b91000.00 in settlement setl_scen_004_2582 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_004_2582')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=-100000)"
        ],
        "ai_confidence": "LOW (0.31)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "REJECTED",
        "constraints_passed": 3,
        "constraints_total": 5,
        "final_decision": "ESCALATE",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": {
        "escalation_reason": "No valid causal evidence chain satisfies all 5 deterministic financial constraints.",
        "rejection_summary": [
          "\u2717 Monetary explanation incomplete or missing",
          "\u2717 Unverified settlement foreign key relationship",
          "\u2717 Decoy transactions rejected by temporal bounds check"
        ],
        "recommended_action": "Route to Tier-2 Financial Operations Audit Queue.",
        "safety_guarantee": "System safely escalated rather than falsely closing financial variance (0% false closure invariant)."
      }
    },
    {
      "scenario_id": "AG-010_IRRELEVANT_EVIDENCE_TRAP",
      "case_id": "CASE-AG-010",
      "settlement_id": "setl_scen_002_8398",
      "category": "Agentic Investigation",
      "expected_outcome": "ESCALATE",
      "expected_amount_inr": 5311.2,
      "actual_bank_credit_inr": 2811.2,
      "variance_inr": -2500.0,
      "variance_paise": -250000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L2",
      "evidence_nodes": [],
      "rejected_decoys": [
        {
          "evidence_id": "E-008_DECOY",
          "entity_type": "REFUND",
          "entity_key": "ref_scen_008_outdated",
          "amount_inr": -2500.0,
          "relationship_path": "Refund ref_scen_008_outdated \u2192 Payment pay_old_301 \u2192 Settlement setl_scen_002_8398",
          "source_file": "refunds.csv",
          "sheet": "Refunds_FY24_Archive",
          "row": 67,
          "cell": "F67",
          "record_hash": "0e3d0445b179f94af9a4447f499321d9525e10ce18628642dcedce7d5fbeb129",
          "evidence_level": "L2",
          "status": "REJECTED",
          "rejection_reason": "Temporal Cut-off Violation: Refund timestamp is 14 days prior to settlement batch cut-off",
          "lesson": "Plausible \u2260 Proven. System rejects out-of-window decoys and safely escalates."
        }
      ],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Candidate event matched variance amount",
          "status": "PASS",
          "rule": "amount_heuristic"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked payment found in historic index",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "VIOLATION: Event occurred 14 days prior (limit: 48h)",
          "status": "FAIL",
          "rule": "temporal_horizon_exceeded"
        },
        {
          "name": "State Validity",
          "description": "State verified",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Source file belongs to archived FY24 batch",
          "status": "FAIL",
          "rule": "stale_provenance"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b92500.00 in settlement setl_scen_002_8398 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_002_8398')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=-250000)"
        ],
        "ai_confidence": "LOW (0.31)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "REJECTED",
        "constraints_passed": 3,
        "constraints_total": 5,
        "final_decision": "ESCALATE",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": {
        "escalation_reason": "No valid causal evidence chain satisfies all 5 deterministic financial constraints.",
        "rejection_summary": [
          "\u2717 Monetary explanation incomplete or missing",
          "\u2717 Unverified settlement foreign key relationship",
          "\u2717 Decoy transactions rejected by temporal bounds check"
        ],
        "recommended_action": "Route to Tier-2 Financial Operations Audit Queue.",
        "safety_guarantee": "System safely escalated rather than falsely closing financial variance (0% false closure invariant)."
      }
    },
    {
      "scenario_id": "AG-011_CONTRADICTORY_TOOL_RESULTS",
      "case_id": "CASE-AG-011",
      "settlement_id": "setl_scen_002_8398",
      "category": "Agentic Investigation",
      "expected_outcome": "ESCALATE",
      "expected_amount_inr": 5311.2,
      "actual_bank_credit_inr": 2811.2,
      "variance_inr": -2500.0,
      "variance_paise": -250000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L2",
      "evidence_nodes": [],
      "rejected_decoys": [
        {
          "evidence_id": "E-008_DECOY",
          "entity_type": "REFUND",
          "entity_key": "ref_scen_008_outdated",
          "amount_inr": -2500.0,
          "relationship_path": "Refund ref_scen_008_outdated \u2192 Payment pay_old_301 \u2192 Settlement setl_scen_002_8398",
          "source_file": "refunds.csv",
          "sheet": "Refunds_FY24_Archive",
          "row": 70,
          "cell": "F70",
          "record_hash": "0e3d0445b179f94af9a4447f499321d9525e10ce18628642dcedce7d5fbeb129",
          "evidence_level": "L2",
          "status": "REJECTED",
          "rejection_reason": "Temporal Cut-off Violation: Refund timestamp is 14 days prior to settlement batch cut-off",
          "lesson": "Plausible \u2260 Proven. System rejects out-of-window decoys and safely escalates."
        }
      ],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Candidate event matched variance amount",
          "status": "PASS",
          "rule": "amount_heuristic"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked payment found in historic index",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "VIOLATION: Event occurred 14 days prior (limit: 48h)",
          "status": "FAIL",
          "rule": "temporal_horizon_exceeded"
        },
        {
          "name": "State Validity",
          "description": "State verified",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Source file belongs to archived FY24 batch",
          "status": "FAIL",
          "rule": "stale_provenance"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b92500.00 in settlement setl_scen_002_8398 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_002_8398')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=-250000)"
        ],
        "ai_confidence": "LOW (0.31)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "REJECTED",
        "constraints_passed": 3,
        "constraints_total": 5,
        "final_decision": "ESCALATE",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": {
        "escalation_reason": "No valid causal evidence chain satisfies all 5 deterministic financial constraints.",
        "rejection_summary": [
          "\u2717 Monetary explanation incomplete or missing",
          "\u2717 Unverified settlement foreign key relationship",
          "\u2717 Decoy transactions rejected by temporal bounds check"
        ],
        "recommended_action": "Route to Tier-2 Financial Operations Audit Queue.",
        "safety_guarantee": "System safely escalated rather than falsely closing financial variance (0% false closure invariant)."
      }
    },
    {
      "scenario_id": "AG-012_CONFIDENT_BUT_WRONG_AI",
      "case_id": "CASE-AG-012",
      "settlement_id": "setl_scen_008_2140",
      "category": "Agentic Investigation",
      "expected_outcome": "ESCALATE",
      "expected_amount_inr": 7716.8,
      "actual_bank_credit_inr": 5716.8,
      "variance_inr": -2000.0,
      "variance_paise": -200000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L2",
      "evidence_nodes": [],
      "rejected_decoys": [
        {
          "evidence_id": "E-008_DECOY",
          "entity_type": "REFUND",
          "entity_key": "ref_scen_008_outdated",
          "amount_inr": -2000.0,
          "relationship_path": "Refund ref_scen_008_outdated \u2192 Payment pay_old_301 \u2192 Settlement setl_scen_008_2140",
          "source_file": "refunds.csv",
          "sheet": "Refunds_FY24_Archive",
          "row": 73,
          "cell": "F73",
          "record_hash": "626ef07e470d26eb2a3b5aff6a058610bfee11178d65443f3ac392193f073758",
          "evidence_level": "L2",
          "status": "REJECTED",
          "rejection_reason": "Temporal Cut-off Violation: Refund timestamp is 14 days prior to settlement batch cut-off",
          "lesson": "Plausible \u2260 Proven. System rejects out-of-window decoys and safely escalates."
        }
      ],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Candidate event matched variance amount",
          "status": "PASS",
          "rule": "amount_heuristic"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked payment found in historic index",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "VIOLATION: Event occurred 14 days prior (limit: 48h)",
          "status": "FAIL",
          "rule": "temporal_horizon_exceeded"
        },
        {
          "name": "State Validity",
          "description": "State verified",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Source file belongs to archived FY24 batch",
          "status": "FAIL",
          "rule": "stale_provenance"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b92000.00 in settlement setl_scen_008_2140 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_008_2140')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=-200000)"
        ],
        "ai_confidence": "LOW (0.31)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "REJECTED",
        "constraints_passed": 3,
        "constraints_total": 5,
        "final_decision": "ESCALATE",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": {
        "escalation_reason": "No valid causal evidence chain satisfies all 5 deterministic financial constraints.",
        "rejection_summary": [
          "\u2717 Monetary explanation incomplete or missing",
          "\u2717 Unverified settlement foreign key relationship",
          "\u2717 Decoy transactions rejected by temporal bounds check"
        ],
        "recommended_action": "Route to Tier-2 Financial Operations Audit Queue.",
        "safety_guarantee": "System safely escalated rather than falsely closing financial variance (0% false closure invariant)."
      }
    },
    {
      "scenario_id": "AG-013_BUDGET_EXHAUSTION",
      "case_id": "CASE-AG-013",
      "settlement_id": "setl_scen_004_2582",
      "category": "Agentic Investigation",
      "expected_outcome": "ESCALATE",
      "expected_amount_inr": 13646.0,
      "actual_bank_credit_inr": 12646.0,
      "variance_inr": -1000.0,
      "variance_paise": -100000,
      "primary_cause": "UNEXPLAINED",
      "evidence_level": "L2",
      "evidence_nodes": [],
      "rejected_decoys": [
        {
          "evidence_id": "E-008_DECOY",
          "entity_type": "REFUND",
          "entity_key": "ref_scen_008_outdated",
          "amount_inr": -1000.0,
          "relationship_path": "Refund ref_scen_008_outdated \u2192 Payment pay_old_301 \u2192 Settlement setl_scen_004_2582",
          "source_file": "refunds.csv",
          "sheet": "Refunds_FY24_Archive",
          "row": 76,
          "cell": "F76",
          "record_hash": "c3c66d558779d3b91047bf0fd9f069c0c04f232e9207639b155bba073d65885b",
          "evidence_level": "L2",
          "status": "REJECTED",
          "rejection_reason": "Temporal Cut-off Violation: Refund timestamp is 14 days prior to settlement batch cut-off",
          "lesson": "Plausible \u2260 Proven. System rejects out-of-window decoys and safely escalates."
        }
      ],
      "constraint_checks": [
        {
          "name": "Monetary Balance",
          "description": "Candidate event matched variance amount",
          "status": "PASS",
          "rule": "amount_heuristic"
        },
        {
          "name": "Settlement Membership",
          "description": "Linked payment found in historic index",
          "status": "PASS",
          "rule": "foreign_key_verified"
        },
        {
          "name": "Temporal Window",
          "description": "VIOLATION: Event occurred 14 days prior (limit: 48h)",
          "status": "FAIL",
          "rule": "temporal_horizon_exceeded"
        },
        {
          "name": "State Validity",
          "description": "State verified",
          "status": "PASS",
          "rule": "state_terminal_success"
        },
        {
          "name": "Provenance Chain",
          "description": "Source file belongs to archived FY24 batch",
          "status": "FAIL",
          "rule": "stale_provenance"
        }
      ],
      "ai_hypothesis": {
        "proposed_explanation": "Variance of \u20b91000.00 in settlement setl_scen_004_2582 is caused by UNEXPLAINED.",
        "tools_requested": [
          "retrieve_entities_by_settlement('setl_scen_004_2582')",
          "query_temporal_window(start='-48h', end='cut_off')",
          "validate_monetary_offset(target=-100000)"
        ],
        "ai_confidence": "LOW (0.31)",
        "ai_status": "PROPOSED_HYPOTHESIS"
      },
      "verifier_outcome": {
        "verdict": "REJECTED",
        "constraints_passed": 3,
        "constraints_total": 5,
        "final_decision": "ESCALATE",
        "authority_note": "Deterministic verifier evaluated all mathematical, temporal, relational, and cryptographic constraints before issuing terminal status."
      },
      "escalation_info": {
        "escalation_reason": "No valid causal evidence chain satisfies all 5 deterministic financial constraints.",
        "rejection_summary": [
          "\u2717 Monetary explanation incomplete or missing",
          "\u2717 Unverified settlement foreign key relationship",
          "\u2717 Decoy transactions rejected by temporal bounds check"
        ],
        "recommended_action": "Route to Tier-2 Financial Operations Audit Queue.",
        "safety_guarantee": "System safely escalated rather than falsely closing financial variance (0% false closure invariant)."
      }
    }
  ]
};
