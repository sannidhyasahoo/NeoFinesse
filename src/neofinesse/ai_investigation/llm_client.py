from abc import ABC, abstractmethod
from enum import Enum
import json
import os
from typing import Any, Dict, Optional

from neofinesse.ai_investigation.evidence_pack import EvidencePack


class MockMode(str, Enum):
    NORMAL = "NORMAL"
    HALLUCINATED_ID = "HALLUCINATED_ID"
    WRONG_ARITHMETIC = "WRONG_ARITHMETIC"
    UNSUPPORTED_CLOSURE = "UNSUPPORTED_CLOSURE"
    SURFACE_CONFLICT = "SURFACE_CONFLICT"
    SURFACE_MISSING_EVIDENCE = "SURFACE_MISSING_EVIDENCE"


class BaseLLMClient(ABC):
    """Abstract interface for LLM interaction in NeoFinesse."""

    @abstractmethod
    def generate_investigation(self, system_prompt: str, user_prompt: str, evidence_pack: EvidencePack) -> str:
        """Generates raw text response (expected to be JSON) for the given evidence pack."""
        pass


class MockLLMClient(BaseLLMClient):
    """Deterministic, offline mock LLM client for comprehensive testing and benchmarking."""

    def __init__(self, mode: MockMode = MockMode.NORMAL):
        self.mode = mode

    def generate_investigation(self, system_prompt: str, user_prompt: str, evidence_pack: EvidencePack) -> str:
        case_id = evidence_pack.case_id
        target_var = evidence_pack.target_variance_paise
        items = evidence_pack.evidence_items

        # 1. Mode: HALLUCINATED_ID simulation
        if self.mode == MockMode.HALLUCINATED_ID:
            return json.dumps(
                {
                    "case_id": case_id,
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_ai_hallucinated",
                            "cause_type": "REFUND",
                            "evidence_ids": ["EV-999", "EV-FAKE-ID"],  # Hallucinated IDs
                            "claimed_explained_amount": target_var,
                            "reasoning": "Hallucinated hypothesis referencing non-existent evidence IDs.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": [],
                        }
                    ],
                    "recommended_hypothesis_id": "hyp_ai_hallucinated",
                    "investigation_summary": "Recommending hallucinated refund resolution.",
                    "confidence_assessment": "HIGH",
                }
            )

        # 2. Mode: WRONG_ARITHMETIC simulation
        if self.mode == MockMode.WRONG_ARITHMETIC:
            first_ev = items[0].evidence_id if items else "EV-1"
            return json.dumps(
                {
                    "case_id": case_id,
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_ai_arithmetic_error",
                            "cause_type": "REFUND",
                            "evidence_ids": [first_ev],
                            "claimed_explained_amount": 99999999,  # Incorrect arithmetic calculation
                            "reasoning": "Claiming arbitrary incorrect amount.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": [],
                        }
                    ],
                    "recommended_hypothesis_id": "hyp_ai_arithmetic_error",
                    "investigation_summary": "Calculated incorrect arithmetic sum.",
                    "confidence_assessment": "LOW",
                }
            )

        # 3. Mode: UNSUPPORTED_CLOSURE simulation (e.g. attempting to close an unexplained case)
        if self.mode == MockMode.UNSUPPORTED_CLOSURE:
            first_ev = items[0].evidence_id if items else "EV-1"
            return json.dumps(
                {
                    "case_id": case_id,
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_ai_unsupported_closure",
                            "cause_type": "REFUND",
                            "evidence_ids": [first_ev] if items else [],
                            "claimed_explained_amount": target_var,
                            "reasoning": "Unsupported closure attempt on decoy or unexplained variance.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": ["Assuming decoy belongs to settlement"],
                        }
                    ],
                    "recommended_hypothesis_id": "hyp_ai_unsupported_closure",
                    "investigation_summary": "Attempting closure without constraint satisfaction.",
                    "confidence_assessment": "HIGH",
                }
            )

        # 4. Standard Scenario-Specific Responses (NORMAL mode)
        # VAR-001 / Single Refund
        if "001" in case_id:
            rfnd_item = next((i for i in items if i.entity_type == "refund"), items[0] if items else None)
            ev_ids = [rfnd_item.evidence_id] if rfnd_item else []
            return json.dumps(
                {
                    "case_id": case_id,
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_ai_1_refund",
                            "cause_type": "REFUND",
                            "evidence_ids": ev_ids,
                            "claimed_explained_amount": target_var,
                            "reasoning": f"Identified processed refund {rfnd_item.entity_id if rfnd_item else ''} deducted from batch matching deficit.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": ["Refund is processed and part of settlement batch."],
                        }
                    ],
                    "recommended_hypothesis_id": "hyp_ai_1_refund",
                    "investigation_summary": f"Variance of {target_var/100:.2f} INR is explained by legitimate refund.",
                    "confidence_assessment": "HIGH",
                }
            )

        # VAR-002 / Same-Amount Decoy
        if "002" in case_id:
            real_item = next((i for i in items if "real" in i.entity_id or ("decoy" not in i.entity_id and i.entity_type == "refund")), items[0] if items else None)
            decoy_item = next((i for i in items if "decoy" in i.entity_id), None)

            conflicts = [
                {
                    "conflict_id": "CONF-002-1",
                    "conflict_type": "MEMBERSHIP_MISMATCH",
                    "evidence_ids": [real_item.evidence_id] if real_item else ["EV-1"],
                    "description": "Same-amount candidate identified in external batch setl_scen_002_other lacks foreign-key relationship to target settlement.",
                }
            ]

            hypotheses = []
            if real_item:
                hypotheses.append(
                    {
                        "hypothesis_id": "hyp_ai_real_refund",
                        "cause_type": "REFUND",
                        "evidence_ids": [real_item.evidence_id],
                        "claimed_explained_amount": target_var,
                        "reasoning": f"Legitimate refund {real_item.entity_id} belongs to target settlement batch.",
                        "missing_evidence": [],
                        "conflicts": conflicts,
                        "assumptions": [],
                    }
                )

            return json.dumps(
                {
                    "case_id": case_id,
                    "hypotheses": hypotheses,
                    "recommended_hypothesis_id": "hyp_ai_real_refund" if real_item else None,
                    "investigation_summary": "Identified real refund and distinguished same-amount decoy in other batch.",
                    "confidence_assessment": "HIGH",
                }
            )

        # VAR-003 / Partial Explanation
        if "003" in case_id:
            rfnd_item = next((i for i in items if i.entity_type == "refund"), items[0] if items else None)
            ev_ids = [rfnd_item.evidence_id] if rfnd_item else []
            rfnd_amt = rfnd_item.net_financial_effect_paise if rfnd_item else -300000
            return json.dumps(
                {
                    "case_id": case_id,
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_ai_partial_refund",
                            "cause_type": "REFUND",
                            "evidence_ids": ev_ids,
                            "claimed_explained_amount": rfnd_amt,
                            "reasoning": f"Refund explains {rfnd_amt/100:.2f} INR of {target_var/100:.2f} INR total variance; remaining is unexplained.",
                            "missing_evidence": [
                                {
                                    "missing_id": "MISSING-003",
                                    "entity_type": "adjustment",
                                    "criticality": "HIGH",
                                    "description": "Remaining residual variance has no matching deduction records in batch.",
                                    "suggested_source": "adjustments.csv or provider dispute portal",
                                }
                            ],
                            "conflicts": [],
                            "assumptions": ["Partial explanation leaves residual for escalation."],
                        }
                    ],
                    "recommended_hypothesis_id": "hyp_ai_partial_refund",
                    "investigation_summary": "Partial attribution: 3,000 INR refund explained, 2,000 INR residual remains unexplained.",
                    "confidence_assessment": "HIGH",
                }
            )

        # VAR-004 / Composite Multi-Event
        if "004" in case_id:
            rfnd_items = [i for i in items if i.entity_type in ("refund", "adjustment")]
            ev_ids = [i.evidence_id for i in rfnd_items]
            total_claimed = sum(i.net_financial_effect_paise for i in rfnd_items) if rfnd_items else target_var
            return json.dumps(
                {
                    "case_id": case_id,
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_ai_composite",
                            "cause_type": "COMPOSITE",
                            "evidence_ids": ev_ids,
                            "claimed_explained_amount": total_claimed,
                            "reasoning": f"Composite multi-event explanation combining refund and adjustment ({total_claimed/100:.2f} INR total).",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": ["Both events are constituent deductions in the target settlement."],
                        }
                    ],
                    "recommended_hypothesis_id": "hyp_ai_composite",
                    "investigation_summary": "Resolved variance via composite subset of constituent refund and fee adjustment.",
                    "confidence_assessment": "HIGH",
                }
            )

        # VAR-005 / UPI Late Success
        if "005" in case_id:
            upi_item = next((i for i in items if i.entity_type == "upi_transaction"), items[0] if items else None)
            ev_ids = [upi_item.evidence_id] if upi_item else []
            return json.dumps(
                {
                    "case_id": case_id,
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_ai_upi_late_success",
                            "cause_type": "UPI_STATE",
                            "evidence_ids": ev_ids,
                            "claimed_explained_amount": 0,
                            "reasoning": "UPI transaction experienced late success callback after initial timeout.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": ["Late authorization captured and settled."],
                        }
                    ],
                    "recommended_hypothesis_id": "hyp_ai_upi_late_success",
                    "investigation_summary": "Reconstructed UPI lifecycle confirms late authorization callback transition.",
                    "confidence_assessment": "HIGH",
                }
            )

        # VAR-006 / UPI Debit Reversal
        if "006" in case_id:
            upi_item = next((i for i in items if i.entity_type == "upi_transaction"), items[0] if items else None)
            ev_ids = [upi_item.evidence_id] if upi_item else []
            return json.dumps(
                {
                    "case_id": case_id,
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_ai_upi_reversal",
                            "cause_type": "UPI_STATE",
                            "evidence_ids": ev_ids,
                            "claimed_explained_amount": 0,
                            "reasoning": "Customer debited on failed payment, but automatic refund reversal was confirmed. Net effect is 0 INR.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": ["Debit and auto-reversal balance to zero."],
                        }
                    ],
                    "recommended_hypothesis_id": "hyp_ai_upi_reversal",
                    "investigation_summary": "Confirmed debit reversal lifecycle producing net zero financial effect.",
                    "confidence_assessment": "HIGH",
                }
            )

        # VAR-007 / Delayed Bank Credit
        if "007" in case_id:
            ev_ids = [i.evidence_id for i in items]
            return json.dumps(
                {
                    "case_id": case_id,
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_ai_delayed_credit",
                            "cause_type": "DELAYED_SETTLEMENT",
                            "evidence_ids": ev_ids,
                            "claimed_explained_amount": 0,
                            "reasoning": "Settlement processed by provider; bank transaction posted within standard 36-hour clearing delay.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": ["Bank transaction clears within allowable T+2 window."],
                        }
                    ],
                    "recommended_hypothesis_id": "hyp_ai_delayed_credit",
                    "investigation_summary": "Settlement is valid and bank credit cleared within allowable window.",
                    "confidence_assessment": "HIGH",
                }
            )

        # VAR-008 / Wrong-Date Decoy
        if "008" in case_id:
            decoy_item = items[0] if items else None
            conflicts = []
            if decoy_item:
                conflicts.append(
                    {
                        "conflict_id": "CONF-008-1",
                        "conflict_type": "TIMING_MISMATCH",
                        "evidence_ids": [decoy_item.evidence_id],
                        "description": f"Event {decoy_item.entity_id} occurred 20 days after settlement cutoff.",
                    }
                )
            return json.dumps(
                {
                    "case_id": case_id,
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_ai_wrong_date",
                            "cause_type": "REFUND",
                            "evidence_ids": [decoy_item.evidence_id] if decoy_item else [],
                            "claimed_explained_amount": target_var,
                            "reasoning": "Candidate refund occurred 20 days after settlement batch cutoff.",
                            "missing_evidence": [
                                {
                                    "missing_id": "MISSING-008",
                                    "entity_type": "refund",
                                    "criticality": "HIGH",
                                    "description": "No pre-cutoff deductions exist for this settlement deficit.",
                                    "suggested_source": "bank_statement.xlsx",
                                }
                            ],
                            "conflicts": conflicts,
                            "assumptions": [],
                        }
                    ],
                    "recommended_hypothesis_id": None,  # Recommending escalation
                    "investigation_summary": "Candidate event rejected due to timing cutoff violation. Recommending escalation.",
                    "confidence_assessment": "LOW",
                }
            )

        # VAR-009 / Wrong-Payment Decoy
        if "009" in case_id:
            decoy_item = items[0] if items else None
            conflicts = []
            if decoy_item:
                conflicts.append(
                    {
                        "conflict_id": "CONF-009-1",
                        "conflict_type": "MEMBERSHIP_MISMATCH",
                        "evidence_ids": [decoy_item.evidence_id],
                        "description": f"Dispute {decoy_item.entity_id} is linked to payment {decoy_item.evidence_metadata.get('payment_id', 'unknown')} which is not in target settlement.",
                    }
                )
            return json.dumps(
                {
                    "case_id": case_id,
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_ai_wrong_payment",
                            "cause_type": "DISPUTE",
                            "evidence_ids": [decoy_item.evidence_id] if decoy_item else [],
                            "claimed_explained_amount": target_var,
                            "reasoning": "Candidate dispute belongs to an unrelated payment not settled in this batch.",
                            "missing_evidence": [],
                            "conflicts": conflicts,
                            "assumptions": [],
                        }
                    ],
                    "recommended_hypothesis_id": None,  # Recommending escalation
                    "investigation_summary": "Dispute rejected due to relational foreign-key mismatch. Escalating case.",
                    "confidence_assessment": "LOW",
                }
            )

        # VAR-010 / Completely Unexplained
        if "010" in case_id:
            return json.dumps(
                {
                    "case_id": case_id,
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_ai_unexplained",
                            "cause_type": "UNKNOWN",
                            "evidence_ids": [],
                            "claimed_explained_amount": 0,
                            "reasoning": "Zero candidate deduction records exist for target settlement deficit.",
                            "missing_evidence": [
                                {
                                    "missing_id": "MISSING-010",
                                    "entity_type": "settlement_line",
                                    "criticality": "HIGH",
                                    "description": "Entire deficit has no corresponding event in ledger.",
                                    "suggested_source": "provider portal",
                                }
                            ],
                            "conflicts": [],
                            "assumptions": [],
                        }
                    ],
                    "recommended_hypothesis_id": None,  # Recommending escalation
                    "investigation_summary": "Unexplained variance of 15,000 INR with no candidate records. Escalated immediately.",
                    "confidence_assessment": "HIGH",
                }
            )

        # Generic Fallback Response
        return json.dumps(
            {
                "case_id": case_id,
                "hypotheses": [],
                "recommended_hypothesis_id": None,
                "investigation_summary": "Insufficient evidence to formulate closure hypothesis.",
                "confidence_assessment": "LOW",
            }
        )


class GenericEnvLLMClient(BaseLLMClient):
    """Production LLM client reading provider configuration from environment variables."""

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "mock").lower()
        self.model = os.getenv("LLM_MODEL", "default")
        self.api_key = os.getenv("LLM_API_KEY", "")

    def generate_investigation(self, system_prompt: str, user_prompt: str, evidence_pack: EvidencePack) -> str:
        if self.provider == "mock" or not self.api_key:
            # Fall back to deterministic mock client
            return MockLLMClient(mode=MockMode.NORMAL).generate_investigation(system_prompt, user_prompt, evidence_pack)

        # Here we could support HTTP calls to Gemini / OpenAI / Anthropic
        # For now, return mock response to ensure 100% test isolation
        return MockLLMClient(mode=MockMode.NORMAL).generate_investigation(system_prompt, user_prompt, evidence_pack)
