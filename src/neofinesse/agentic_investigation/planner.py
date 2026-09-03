from abc import ABC, abstractmethod
import json
import os
from typing import Any, Dict, Optional

from neofinesse.agentic_investigation.models import AgentInvestigationStatus
from neofinesse.agentic_investigation.state import InvestigationState
from neofinesse.ai_investigation.evidence_pack import EvidencePack
from neofinesse.ai_investigation.llm_client import MockMode


class BaseAgentPlanner(ABC):
    """Abstract interface for multi-round agentic investigation planning."""

    @abstractmethod
    def plan_round(
        self,
        system_prompt: str,
        user_prompt: str,
        state: InvestigationState,
        pack: EvidencePack,
    ) -> str:
        """Returns structured JSON text adhering to AgentRoundResponse schema."""
        pass


class LiveAgentPlanner(BaseAgentPlanner):
    """Live agent planner dispatching investigation prompts to a BaseLLMClient implementation."""

    def __init__(self, llm_client: Optional[Any] = None):
        if llm_client is None:
            from neofinesse.agentic_investigation.llm_client import GenericLLMClient
            self.llm_client = GenericLLMClient()
        else:
            self.llm_client = llm_client
        self.last_response_metadata: Optional[Any] = None

    def plan_round(
        self,
        system_prompt: str,
        user_prompt: str,
        state: InvestigationState,
        pack: EvidencePack,
    ) -> str:
        meta = self.llm_client.generate_with_metadata(prompt=user_prompt, system_prompt=system_prompt)
        self.last_response_metadata = meta
        if meta.error:
            if "timeout" in meta.error.lower():
                raise TimeoutError(meta.error)
            raise RuntimeError(f"LLM_GENERATION_FAILED: {meta.error}")
        return meta.text


class MockAgentPlanner(BaseAgentPlanner):
    """Deterministic mock agent planner for comprehensive offline testing of agentic loops."""

    def __init__(self, mode: MockMode = MockMode.NORMAL):
        self.mode = mode
        self.last_response_metadata: Optional[Any] = None

    def plan_round(
        self,
        system_prompt: str,
        user_prompt: str,
        state: InvestigationState,
        pack: EvidencePack,
    ) -> str:
        case_id = state.case_id
        target_var = state.target_variance
        current_round = state.round_number
        items = list(state.current_evidence.values())

        # 1. Failure Mode Testing
        if self.mode == MockMode.HALLUCINATED_ID:
            return json.dumps(
                {
                    "status": "SUFFICIENT",
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_hallucinated",
                            "cause_type": "REFUND",
                            "evidence_ids": ["EV-9999"],  # Hallucinated ID
                            "claimed_explained_amount": target_var,
                            "reasoning": "Hallucinated hypothesis referencing non-existent ID",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": [],
                        }
                    ],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": "hyp_hallucinated",
                    "conflicts": [],
                    "missing_evidence": [],
                    "reasoning": "Attempting hallucinated hypothesis.",
                }
            )

        if self.mode == MockMode.UNSUPPORTED_CLOSURE:
            ev_id = items[0].evidence_id if items else "EV-1"
            return json.dumps(
                {
                    "status": "SUFFICIENT",
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_unsupported",
                            "cause_type": "REFUND",
                            "evidence_ids": [ev_id],
                            "claimed_explained_amount": target_var,
                            "reasoning": "Attempting unsupported closure on unverified candidate.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": [],
                        }
                    ],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": "hyp_unsupported",
                    "conflicts": [],
                    "missing_evidence": [],
                    "reasoning": "Attempting unsupported closure.",
                }
            )

        # 2. Agentic Scenarios (AG-001 through AG-008)

        # AG-001: Missing Membership Verification
        if "AG-001" in case_id:
            adj_item = next((i for i in items if i.entity_type == "adjustment"), None)
            rfnd_item = next((i for i in items if i.entity_type == "refund"), None)
            adj_id = adj_item.entity_id if adj_item else "adj_scen_004"

            if current_round == 1:
                return json.dumps(
                    {
                        "status": "NEEDS_EVIDENCE",
                        "hypotheses": [],
                        "investigation_requests": [
                            {
                                "request_id": "REQ-AG001-1",
                                "tool": "verify_membership",
                                "arguments": {
                                    "event_id": adj_id,
                                    "settlement_id": state.settlement_id,
                                },
                                "reason": "Verify if candidate adjustment belongs to target settlement batch.",
                            }
                        ],
                        "recommended_hypothesis_id": None,
                        "conflicts": [],
                        "missing_evidence": ["Settlement membership for candidate adjustment"],
                        "reasoning": "Identified candidate adjustment; requesting membership verification before attributing variance.",
                    }
                )
            else:
                ev_ids = [i.evidence_id for i in (rfnd_item, adj_item) if i]
                total_effect = sum(i.net_financial_effect_paise for i in (rfnd_item, adj_item) if i)
                return json.dumps(
                    {
                        "status": "SUFFICIENT",
                        "hypotheses": [
                            {
                                "hypothesis_id": "hyp_ag001_composite",
                                "cause_type": "COMPOSITE",
                                "evidence_ids": ev_ids,
                                "claimed_explained_amount": total_effect if total_effect != 0 else target_var,
                                "reasoning": "Confirmed membership of adjustment; composite refund and adjustment explain variance.",
                                "missing_evidence": [],
                                "conflicts": [],
                                "assumptions": ["Both deductions verified as batch members."],
                            }
                        ],
                        "investigation_requests": [],
                        "recommended_hypothesis_id": "hyp_ag001_composite",
                        "conflicts": [],
                        "missing_evidence": [],
                        "reasoning": "Membership verified via tool; proposing composite resolution.",
                    }
                )

        # AG-002: Wrong Membership (Hypothesis Revision)
        if "AG-002" in case_id:
            if current_round == 1:
                return json.dumps(
                    {
                        "status": "NEEDS_EVIDENCE",
                        "hypotheses": [
                            {
                                "hypothesis_id": "hyp_ag002_initial",
                                "cause_type": "ADJUSTMENT",
                                "evidence_ids": [items[0].evidence_id] if items else [],
                                "claimed_explained_amount": target_var,
                                "reasoning": "Candidate adjustment matches variance amount.",
                                "missing_evidence": ["Batch membership"],
                                "conflicts": [],
                                "assumptions": ["Assumed membership"],
                            }
                        ],
                        "investigation_requests": [
                            {
                                "request_id": "REQ-AG002-1",
                                "tool": "verify_membership",
                                "arguments": {
                                    "event_id": "adj_decoy_unrelated",
                                    "settlement_id": state.settlement_id,
                                },
                                "reason": "Check if adjustment is a member of this settlement batch.",
                            }
                        ],
                        "recommended_hypothesis_id": None,
                        "conflicts": [],
                        "missing_evidence": ["Membership confirmation"],
                        "reasoning": "Candidate adjustment requires membership verification.",
                    }
                )
            else:
                return json.dumps(
                    {
                        "status": "ESCALATE",
                        "hypotheses": [],
                        "investigation_requests": [],
                        "recommended_hypothesis_id": None,
                        "conflicts": [
                            {
                                "conflict_id": "CONF-AG002",
                                "conflict_type": "MEMBERSHIP_MISMATCH",
                                "evidence_ids": [items[0].evidence_id] if items else [],
                                "description": "Tool confirmed candidate adjustment is NOT_MEMBER of target settlement batch.",
                            }
                        ],
                        "missing_evidence": ["No valid deduction records exist for target batch."],
                        "reasoning": "Earlier adjustment hypothesis rejected due to confirmed non-membership. Escalating.",
                    }
                )

        # AG-003: Missing UPI History -> Reconstructed Debit Reversal
        if "AG-003" in case_id:
            upi_item = next((i for i in items if i.entity_type == "upi_transaction"), items[0] if items else None)
            upi_id = upi_item.entity_id if upi_item else "upi_scen_006"

            if current_round == 1:
                return json.dumps(
                    {
                        "status": "NEEDS_EVIDENCE",
                        "hypotheses": [],
                        "investigation_requests": [
                            {
                                "request_id": "REQ-AG003-1",
                                "tool": "retrieve_upi_history",
                                "arguments": {
                                    "upi_transaction_id": upi_id,
                                },
                                "reason": "Fetch full chronological lifecycle and reversal state.",
                            }
                        ],
                        "recommended_hypothesis_id": None,
                        "conflicts": [],
                        "missing_evidence": ["UPI state transition sequence"],
                        "reasoning": "Initial evidence indicates failed payment; requesting full lifecycle history.",
                    }
                )
            else:
                ev_ids = [upi_item.evidence_id] if upi_item else []
                return json.dumps(
                    {
                        "status": "SUFFICIENT",
                        "hypotheses": [
                            {
                                "hypothesis_id": "hyp_ag003_reversal",
                                "cause_type": "UPI_STATE",
                                "evidence_ids": ev_ids,
                                "claimed_explained_amount": 0,
                                "reasoning": "UPI history confirms customer was debited and automatically reversed. Net financial effect = 0 INR.",
                                "missing_evidence": [],
                                "conflicts": [],
                                "assumptions": ["Debit and auto-reversal verified from logs."],
                            }
                        ],
                        "investigation_requests": [],
                        "recommended_hypothesis_id": "hyp_ag003_reversal",
                        "conflicts": [],
                        "missing_evidence": [],
                        "reasoning": "Reconstructed lifecycle proves net zero effect.",
                    }
                )

        # AG-004: Late UPI Success
        if "AG-004" in case_id:
            upi_item = next((i for i in items if i.entity_type == "upi_transaction"), items[0] if items else None)
            upi_id = upi_item.entity_id if upi_item else "upi_scen_005"

            if current_round == 1:
                return json.dumps(
                    {
                        "status": "NEEDS_EVIDENCE",
                        "hypotheses": [],
                        "investigation_requests": [
                            {
                                "request_id": "REQ-AG004-1",
                                "tool": "retrieve_upi_history",
                                "arguments": {
                                    "upi_transaction_id": upi_id,
                                },
                                "reason": "Investigate late authorization callback.",
                            }
                        ],
                        "recommended_hypothesis_id": None,
                        "conflicts": [],
                        "missing_evidence": ["UPI callback history"],
                        "reasoning": "Requesting full callback history for timeout payment.",
                    }
                )
            else:
                ev_ids = [upi_item.evidence_id] if upi_item else []
                return json.dumps(
                    {
                        "status": "SUFFICIENT",
                        "hypotheses": [
                            {
                                "hypothesis_id": "hyp_ag004_late_success",
                                "cause_type": "UPI_STATE",
                                "evidence_ids": ev_ids,
                                "claimed_explained_amount": 0,
                                "reasoning": "UPI history confirms late authorization callback after timeout. Captured successfully.",
                                "missing_evidence": [],
                                "conflicts": [],
                                "assumptions": ["Late authorization confirmed."],
                            }
                        ],
                        "investigation_requests": [],
                        "recommended_hypothesis_id": "hyp_ag004_late_success",
                        "conflicts": [],
                        "missing_evidence": [],
                        "reasoning": "Late success verified.",
                    }
                )

        # AG-005: Conflicting Refund Status
        if "AG-005" in case_id:
            if current_round == 1:
                return json.dumps(
                    {
                        "status": "NEEDS_EVIDENCE",
                        "hypotheses": [],
                        "investigation_requests": [
                            {
                                "request_id": "REQ-AG005-1",
                                "tool": "retrieve_source_record",
                                "arguments": {
                                    "source_id": "SRC-REFUNDS",
                                    "record_id": "rfnd_failed_candidate",
                                },
                                "reason": "Inspect underlying refund lifecycle state.",
                            }
                        ],
                        "recommended_hypothesis_id": None,
                        "conflicts": [],
                        "missing_evidence": ["Refund status confirmation"],
                        "reasoning": "Refund amount matches variance, but status is unconfirmed.",
                    }
                )
            else:
                return json.dumps(
                    {
                        "status": "ESCALATE",
                        "hypotheses": [],
                        "investigation_requests": [],
                        "recommended_hypothesis_id": None,
                        "conflicts": [
                            {
                                "conflict_id": "CONF-AG005",
                                "conflict_type": "STATE_MISMATCH",
                                "evidence_ids": [],
                                "description": "Underlying refund record confirmed status FAILED.",
                            }
                        ],
                        "missing_evidence": ["No valid processed refund exists."],
                        "reasoning": "Candidate refund failed; cannot explain settlement deduction. Escalating.",
                    }
                )

        # AG-006: Truly Unexplained Variance
        if "AG-006" in case_id:
            if current_round == 1:
                return json.dumps(
                    {
                        "status": "NEEDS_EVIDENCE",
                        "hypotheses": [],
                        "investigation_requests": [
                            {
                                "request_id": "REQ-AG006-1",
                                "tool": "retrieve_temporal_neighbors",
                                "arguments": {
                                    "entity_id": state.settlement_id,
                                    "reference_timestamp": "2026-08-20T12:00:00",
                                    "window_before_minutes": 120,
                                    "window_after_minutes": 120,
                                },
                                "reason": "Search temporal window for untracked deductions.",
                            }
                        ],
                        "recommended_hypothesis_id": None,
                        "conflicts": [],
                        "missing_evidence": ["No candidate deduction events"],
                        "reasoning": "Searching temporal neighbors.",
                    }
                )
            else:
                return json.dumps(
                    {
                        "status": "ESCALATE",
                        "hypotheses": [],
                        "investigation_requests": [],
                        "recommended_hypothesis_id": None,
                        "conflicts": [],
                        "missing_evidence": ["Zero matching deduction records in ledger"],
                        "reasoning": "Temporal search returned no matching events. Variance is genuinely unexplained. Escalating.",
                    }
                )

        # AG-007: Decoy Explosion
        if "AG-007" in case_id:
            real_item = next((i for i in items if i.entity_type == "refund" and ("real" in i.entity_id or "decoy" not in i.entity_id)), next((i for i in items if i.entity_type == "refund"), items[0] if items else None))

            if current_round == 1:
                return json.dumps(
                    {
                        "status": "NEEDS_EVIDENCE",
                        "hypotheses": [],
                        "investigation_requests": [
                            {
                                "request_id": "REQ-AG007-1",
                                "tool": "verify_membership",
                                "arguments": {
                                    "event_id": real_item.entity_id if real_item else "rfnd_real",
                                    "settlement_id": state.settlement_id,
                                },
                                "reason": "Distinguish genuine deduction from decoy candidates by checking settlement line foreign key.",
                            }
                        ],
                        "recommended_hypothesis_id": None,
                        "conflicts": [
                            {
                                "conflict_id": "CONF-AG007-DECOY",
                                "conflict_type": "MEMBERSHIP_MISMATCH",
                                "evidence_ids": [i.evidence_id for i in items if "decoy" in i.entity_id],
                                "description": "Multiple same-amount candidates detected across different batches.",
                            }
                        ],
                        "missing_evidence": ["Membership verification for candidate"],
                        "reasoning": "Multiple same-amount candidates found; requesting membership verification to prune decoys.",
                    }
                )
            else:
                ev_ids = [real_item.evidence_id] if real_item else []
                return json.dumps(
                    {
                        "status": "SUFFICIENT",
                        "hypotheses": [
                            {
                                "hypothesis_id": "hyp_ag007_resolved",
                                "cause_type": "REFUND",
                                "evidence_ids": ev_ids,
                                "claimed_explained_amount": target_var,
                                "reasoning": f"Verified membership for {real_item.entity_id if real_item else ''}; pruned unrelated same-amount decoys.",
                                "missing_evidence": [],
                                "conflicts": [],
                                "assumptions": ["Real refund verified as batch member."],
                            }
                        ],
                        "investigation_requests": [],
                        "recommended_hypothesis_id": "hyp_ag007_resolved",
                        "conflicts": [],
                        "missing_evidence": [],
                        "reasoning": "Decoys pruned successfully; real refund verified.",
                    }
                )

        # AG-008: Flagship Multi-Step Investigation
        if "AG-008" in case_id:
            rfnd_item = next((i for i in items if i.entity_type == "refund"), None)
            adj_item = next((i for i in items if i.entity_type == "adjustment"), None)

            if current_round == 1:
                return json.dumps(
                    {
                        "status": "NEEDS_EVIDENCE",
                        "hypotheses": [],
                        "investigation_requests": [
                            {
                                "request_id": "REQ-AG008-1",
                                "tool": "retrieve_related_evidence",
                                "arguments": {
                                    "entity_type": "settlement_line",
                                    "entity_id": f"line_pay_{state.settlement_id}",
                                    "relationship": "source_event",
                                },
                                "reason": "Retrieve constituent deductions attached to settlement lines.",
                            }
                        ],
                        "recommended_hypothesis_id": None,
                        "conflicts": [],
                        "missing_evidence": ["Constituent deductions"],
                        "reasoning": "Step 1: Retrieving related settlement events.",
                    }
                )
            elif current_round == 2:
                adj_id = adj_item.entity_id if adj_item else "adj_scen_004"
                return json.dumps(
                    {
                        "status": "NEEDS_EVIDENCE",
                        "hypotheses": [],
                        "investigation_requests": [
                            {
                                "request_id": "REQ-AG008-2",
                                "tool": "verify_membership",
                                "arguments": {
                                    "event_id": adj_id,
                                    "settlement_id": state.settlement_id,
                                },
                                "reason": "Step 2: Confirm adjustment membership.",
                            }
                        ],
                        "recommended_hypothesis_id": None,
                        "conflicts": [],
                        "missing_evidence": ["Adjustment membership"],
                        "reasoning": "Step 2: Verifying membership of retrieved adjustment candidate.",
                    }
                )
            else:
                ev_ids = [i.evidence_id for i in (rfnd_item, adj_item) if i]
                total_effect = sum(i.net_financial_effect_paise for i in (rfnd_item, adj_item) if i)
                return json.dumps(
                    {
                        "status": "SUFFICIENT",
                        "hypotheses": [
                            {
                                "hypothesis_id": "hyp_ag008_composite",
                                "cause_type": "COMPOSITE",
                                "evidence_ids": ev_ids,
                                "claimed_explained_amount": total_effect if total_effect != 0 else target_var,
                                "reasoning": "Multi-step investigation verified composite refund and adjustment explanation.",
                                "missing_evidence": [],
                                "conflicts": [],
                                "assumptions": [],
                            }
                        ],
                        "investigation_requests": [],
                        "recommended_hypothesis_id": "hyp_ag008_composite",
                        "conflicts": [],
                        "missing_evidence": [],
                        "reasoning": "Multi-step verification complete.",
                    }
                )

        # AG-009: Redundant Tool Loop (Adversarial)
        if "AG-009" in case_id:
            if current_round in (1, 2):
                return json.dumps(
                    {
                        "status": "NEEDS_EVIDENCE",
                        "hypotheses": [],
                        "investigation_requests": [
                            {
                                "request_id": f"REQ-AG009-{current_round}",
                                "tool": "verify_membership",
                                "arguments": {
                                    "event_id": "adj_scen_004",
                                    "settlement_id": state.settlement_id,
                                },
                                "reason": "Redundant check: verify membership of adjustment.",
                            }
                        ],
                        "recommended_hypothesis_id": None,
                        "conflicts": [],
                        "missing_evidence": ["Adjustment membership confirmation"],
                        "reasoning": "Attempting redundant query.",
                    }
                )
            else:
                return json.dumps(
                    {
                        "status": "ESCALATE",
                        "hypotheses": [],
                        "investigation_requests": [],
                        "recommended_hypothesis_id": None,
                        "conflicts": [
                            {
                                "conflict_id": "CONF-REDUNDANT-LOOP",
                                "conflict_type": "STATE_MISMATCH",
                                "evidence_ids": [],
                                "description": "Investigation loop prevented infinite recursion on duplicate tool call.",
                            }
                        ],
                        "missing_evidence": ["Tool request rejected as duplicate"],
                        "reasoning": "Duplicate tool call was caught and blocked by validator. Escalating safely.",
                    }
                )

        # AG-010: Irrelevant Evidence Trap (Decoy Flooding)
        if "AG-010" in case_id:
            if current_round == 1:
                return json.dumps(
                    {
                        "status": "NEEDS_EVIDENCE",
                        "hypotheses": [],
                        "investigation_requests": [
                            {
                                "request_id": "REQ-AG010-1",
                                "tool": "verify_membership",
                                "arguments": {
                                    "event_id": "rfnd_unrelated_trap",
                                    "settlement_id": state.settlement_id,
                                },
                                "reason": "Verify candidate from flooded decoy candidates.",
                            }
                        ],
                        "recommended_hypothesis_id": None,
                        "conflicts": [
                            {
                                "conflict_id": "CONF-DECOY-FLOOD",
                                "conflict_type": "MEMBERSHIP_MISMATCH",
                                "evidence_ids": [i.evidence_id for i in items if "decoy" in i.entity_id],
                                "description": "High volume of same-amount decoys from external settlements.",
                            }
                        ],
                        "missing_evidence": ["Verified batch line linkage"],
                        "reasoning": "Flooded with decoy candidates; requesting membership verification.",
                    }
                )
            else:
                return json.dumps(
                    {
                        "status": "ESCALATE",
                        "hypotheses": [],
                        "investigation_requests": [],
                        "recommended_hypothesis_id": None,
                        "conflicts": [
                            {
                                "conflict_id": "CONF-AG010-REJECT",
                                "conflict_type": "MEMBERSHIP_MISMATCH",
                                "evidence_ids": [],
                                "description": "All flooded decoy candidates belong to other settlements.",
                            }
                        ],
                        "missing_evidence": ["No valid deduction member found"],
                        "reasoning": "All candidates were proven to be decoys. Escalating honestly.",
                    }
                )

        # AG-011: Contradictory Tool Results
        if "AG-011" in case_id:
            if current_round == 1:
                return json.dumps(
                    {
                        "status": "NEEDS_EVIDENCE",
                        "hypotheses": [],
                        "investigation_requests": [
                            {
                                "request_id": "REQ-AG011-1",
                                "tool": "retrieve_source_record",
                                "arguments": {
                                    "source_id": "SRC-DISPUTES",
                                    "record_id": "disp_contradictory_record",
                                },
                                "reason": "Verify conflicting gateway vs bank chargeback records.",
                            }
                        ],
                        "recommended_hypothesis_id": None,
                        "conflicts": [
                            {
                                "conflict_id": "CONF-AG011-DISCREPANCY",
                                "conflict_type": "STATE_MISMATCH",
                                "evidence_ids": [],
                                "description": "Gateway reports CAPTURED while bank feed reports CHARGEBACK_REVERSAL.",
                            }
                        ],
                        "missing_evidence": ["Source record verification for chargeback"],
                        "reasoning": "Contradictory state between payment gateway and bank clearing logs.",
                    }
                )
            else:
                return json.dumps(
                    {
                        "status": "ESCALATE",
                        "hypotheses": [],
                        "investigation_requests": [],
                        "recommended_hypothesis_id": None,
                        "conflicts": [
                            {
                                "conflict_id": "CONF-AG011-UNRESOLVED",
                                "conflict_type": "STATE_MISMATCH",
                                "evidence_ids": [],
                                "description": "Contradictory evidence cannot be reconciled automatically.",
                            }
                        ],
                        "missing_evidence": ["Audited bank settlement voucher"],
                        "reasoning": "Irreconcilable contradiction detected across data sources. Mandatory escalation to human controller.",
                    }
                )

        # AG-012: Confident But Wrong AI (Adversarial Verifier Override)
        if "AG-012" in case_id:
            # AI is 100% confident in an invalid candidate (decoy or unrelated batch member)
            decoy_item = next((i for i in items if "decoy" in i.entity_id), items[-1] if items else None)
            ev_ids = [decoy_item.evidence_id] if decoy_item else []
            return json.dumps(
                {
                    "status": "SUFFICIENT",
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_ag012_confident_wrong",
                            "cause_type": "REFUND",
                            "evidence_ids": ev_ids,
                            "claimed_explained_amount": target_var,
                            "reasoning": "AI is 100% confident that this refund explains the variance despite post-cutoff timestamp.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": ["Assuming post-cutoff date is an ignorable logging delay."],
                        }
                    ],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": "hyp_ag012_confident_wrong",
                    "conflicts": [],
                    "missing_evidence": [],
                    "reasoning": "Proposing confident hypothesis.",
                }
            )

        # AG-013: Investigation Budget Exhaustion
        if "AG-013" in case_id:
            return json.dumps(
                {
                    "status": "NEEDS_EVIDENCE",
                    "hypotheses": [],
                    "investigation_requests": [
                        {
                            "request_id": f"REQ-AG013-{current_round}",
                            "tool": "retrieve_related_evidence",
                            "arguments": {
                                "entity_type": "settlement_line",
                                "entity_id": f"line_hop_{current_round}_{state.settlement_id}",
                                "relationship": "source_event",
                            },
                            "reason": f"Hop {current_round}: Searching deep relational dependency.",
                        }
                    ],
                    "recommended_hypothesis_id": None,
                    "conflicts": [],
                    "missing_evidence": [f"Deep hop {current_round} evidence"],
                    "reasoning": f"Investigation hop {current_round} in progress.",
                }
            )

        # 3. Standard Scenarios (VAR-001 to VAR-010)

        # VAR-001: Refund Variance
        if "001" in case_id:
            rfnd_item = next((i for i in items if i.entity_type == "refund"), items[0] if items else None)
            ev_ids = [rfnd_item.evidence_id] if rfnd_item else []
            return json.dumps(
                {
                    "status": "SUFFICIENT",
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_var001_single_refund",
                            "cause_type": "REFUND",
                            "evidence_ids": ev_ids,
                            "claimed_explained_amount": target_var,
                            "reasoning": "Single legitimate processed refund explains entire batch deficit.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": [],
                        }
                    ],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": "hyp_var001_single_refund",
                    "conflicts": [],
                    "missing_evidence": [],
                    "reasoning": "Verified single refund.",
                }
            )

        # VAR-002: Same-Amount Decoy
        if "002" in case_id:
            real_item = next((i for i in items if i.entity_type == "refund" and ("real" in i.entity_id or "decoy" not in i.entity_id)), next((i for i in items if i.entity_type == "refund"), items[0] if items else None))
            ev_ids = [real_item.evidence_id] if real_item else []
            return json.dumps(
                {
                    "status": "SUFFICIENT",
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_var002_real_refund",
                            "cause_type": "REFUND",
                            "evidence_ids": ev_ids,
                            "claimed_explained_amount": target_var,
                            "reasoning": "Real refund is confirmed batch member; decoy refund belongs to another settlement batch.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": ["Real refund verified as batch member."],
                        }
                    ],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": "hyp_var002_real_refund",
                    "conflicts": [
                        {
                            "conflict_id": "CONF-DECOY-002",
                            "conflict_type": "MEMBERSHIP_MISMATCH",
                            "evidence_ids": [i.evidence_id for i in items if "decoy" in i.entity_id],
                            "description": "Decoy refund belongs to another settlement batch.",
                        }
                    ],
                    "missing_evidence": [],
                    "reasoning": "Real refund verified; decoy rejected.",
                }
            )

        # VAR-003: Partial Attribution
        if "003" in case_id:
            rfnd_item = next((i for i in items if i.entity_type == "refund"), items[0] if items else None)
            ev_ids = [rfnd_item.evidence_id] if rfnd_item else []
            rfnd_amt = rfnd_item.net_financial_effect_paise if rfnd_item else -300000
            return json.dumps(
                {
                    "status": "SUFFICIENT",
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_var003_partial",
                            "cause_type": "REFUND",
                            "evidence_ids": ev_ids,
                            "claimed_explained_amount": rfnd_amt,
                            "reasoning": "Refund explains 3,000 INR of 5,000 INR deficit; 2,000 INR residual remains unexplained.",
                            "missing_evidence": ["Remaining 2,000 INR deduction records"],
                            "conflicts": [],
                            "assumptions": [],
                        }
                    ],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": "hyp_var003_partial",
                    "conflicts": [],
                    "missing_evidence": ["Remaining residual deduction records"],
                    "reasoning": "Partial attribution: 3,000 INR refund explained, 2,000 INR escalated.",
                }
            )

        # VAR-004: Multi-Event Composite
        if "004" in case_id:
            rfnd_item = next((i for i in items if i.entity_type == "refund"), None)
            adj_item = next((i for i in items if i.entity_type == "adjustment"), None)
            ev_ids = [i.evidence_id for i in (rfnd_item, adj_item) if i]
            total_effect = sum(i.net_financial_effect_paise for i in (rfnd_item, adj_item) if i)
            return json.dumps(
                {
                    "status": "SUFFICIENT",
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_var004_composite",
                            "cause_type": "COMPOSITE",
                            "evidence_ids": ev_ids,
                            "claimed_explained_amount": total_effect if total_effect != 0 else target_var,
                            "reasoning": "Legitimate refund (-₹700) and risk hold adjustment (-₹300) jointly explain the -₹1,000 deficit.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": ["Both deductions verified as batch members."],
                        }
                    ],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": "hyp_var004_composite",
                    "conflicts": [],
                    "missing_evidence": [],
                    "reasoning": "Composite multi-event explanation verified.",
                }
            )

        # VAR-005: UPI Late Success
        if "005" in case_id:
            upi_item = next((i for i in items if i.entity_type == "upi_transaction"), items[0] if items else None)
            ev_ids = [upi_item.evidence_id] if upi_item else []
            return json.dumps(
                {
                    "status": "SUFFICIENT",
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_var005_late_success",
                            "cause_type": "UPI_STATE",
                            "evidence_ids": ev_ids,
                            "claimed_explained_amount": 0,
                            "reasoning": "UPI transaction received late authorization callback after initial timeout. Payment captured successfully.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": ["Late authorization confirmed via callback log."],
                        }
                    ],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": "hyp_var005_late_success",
                    "conflicts": [],
                    "missing_evidence": [],
                    "reasoning": "Late authorization callback verified.",
                }
            )

        # VAR-006: UPI Debit Reversal
        if "006" in case_id:
            upi_item = next((i for i in items if i.entity_type == "upi_transaction"), items[0] if items else None)
            ev_ids = [upi_item.evidence_id] if upi_item else []
            return json.dumps(
                {
                    "status": "SUFFICIENT",
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_var006_reversal",
                            "cause_type": "UPI_STATE",
                            "evidence_ids": ev_ids,
                            "claimed_explained_amount": 0,
                            "reasoning": "Customer debited but automatic bank reversal succeeded. Final net financial effect is 0 INR.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": ["Debit and auto-reversal verified from NPCI/Bank logs."],
                        }
                    ],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": "hyp_var006_reversal",
                    "conflicts": [],
                    "missing_evidence": [],
                    "reasoning": "UPI debit reversal confirmed.",
                }
            )

        # VAR-007: Delayed Bank Settlement Credit
        if "007" in case_id:
            ev_ids = [i.evidence_id for i in items]
            return json.dumps(
                {
                    "status": "SUFFICIENT",
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_var007_delayed_credit",
                            "cause_type": "DELAYED_SETTLEMENT",
                            "evidence_ids": ev_ids,
                            "claimed_explained_amount": 0,
                            "reasoning": "Settlement processed by provider; bank transaction posted within standard clearing delay.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": [],
                        }
                    ],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": "hyp_var007_delayed_credit",
                    "conflicts": [],
                    "missing_evidence": [],
                    "reasoning": "Delayed bank settlement credit verified.",
                }
            )

        # VAR-008, VAR-009, VAR-010: Decoys & Unexplained Escalations
        if any(scen in case_id for scen in ("008", "009", "010")):
            conf_type = "TIMING_MISMATCH" if "008" in case_id else "MEMBERSHIP_MISMATCH"
            return json.dumps(
                {
                    "status": "ESCALATE",
                    "hypotheses": [],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": None,
                    "conflicts": [
                        {
                            "conflict_id": "CONF-DECOY",
                            "conflict_type": conf_type,
                            "evidence_ids": [items[0].evidence_id] if items else [],
                            "description": "Candidate rejected due to relational or temporal constraint failure.",
                        }
                    ] if "010" not in case_id else [],
                    "missing_evidence": ["No valid deduction records in ledger"],
                    "reasoning": "Candidate decoy fails constraints. Escalating to human controller.",
                }
            )

        # Default Escalation
        return json.dumps(
            {
                "status": "ESCALATE",
                "hypotheses": [],
                "investigation_requests": [],
                "recommended_hypothesis_id": None,
                "conflicts": [],
                "missing_evidence": ["Insufficient evidence"],
                "reasoning": "Insufficient evidence to resolve variance.",
            }
        )
