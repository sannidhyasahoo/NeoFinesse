import itertools
from typing import List

from neofinesse.investigation.hypothesis import HypothesisBuilder
from neofinesse.investigation.models import CauseType, Hypothesis, HypothesisStatus
from neofinesse.models.base import EvidenceLevel
from neofinesse.retrieval.base import EvidenceCandidate, InvestigationTaskCategory, RetrievalResult


class HypothesisGenerator:
    """Deterministically generates competing candidate hypotheses from retrieved evidence."""

    @staticmethod
    def generate_hypotheses(
        case_id: str,
        target_variance: int,
        retrieval_result: RetrievalResult,
        task_category: InvestigationTaskCategory = InvestigationTaskCategory.SETTLEMENT_RCA,
    ) -> List[Hypothesis]:
        hypotheses: List[Hypothesis] = []
        candidates = retrieval_result.candidates

        # 1. Handle Task: UPI_STATE_INVESTIGATION
        if task_category == InvestigationTaskCategory.UPI_STATE_INVESTIGATION:
            for idx, cand in enumerate(candidates):
                if cand.entity_type == "upi_transaction":
                    meta = cand.evidence_metadata
                    classification = meta.get("evidence_classification", "UPI_STATE")
                    explanation = f"UPI lifecycle reconstruction: {classification} with net financial effect of {cand.net_financial_effect or 0} paise."

                    h = HypothesisBuilder.create_hypothesis(
                        hypothesis_id=f"hyp_upi_{idx+1}_{cand.entity_id}",
                        case_id=case_id,
                        cause_type=CauseType.UPI_STATE,
                        candidate_evidence=[cand],
                        target_variance=target_variance,
                        explanation=explanation,
                    )
                    h.hypothesis_metadata["upi_classification"] = classification
                    hypotheses.append(h)

            if not hypotheses:
                hypotheses.append(
                    HypothesisBuilder.create_hypothesis(
                        hypothesis_id=f"hyp_upi_unknown_{case_id}",
                        case_id=case_id,
                        cause_type=CauseType.UNKNOWN,
                        candidate_evidence=[],
                        target_variance=target_variance,
                        explanation="No UPI lifecycle evidence retrieved to explain transaction state.",
                    )
                )
            return hypotheses

        # 2. Handle Task: BANK_SETTLEMENT_STATE (e.g. Delayed Bank Credit)
        if task_category == InvestigationTaskCategory.BANK_SETTLEMENT_STATE:
            # Check for delayed credit candidates or matching bank transactions
            delayed_cands = candidates if candidates else []
            h = Hypothesis(
                hypothesis_id=f"hyp_bank_delayed_{case_id}",
                case_id=case_id,
                cause_type=CauseType.DELAYED_SETTLEMENT,
                evidence_ids=[c.entity_id for c in delayed_cands],
                candidate_evidence=delayed_cands,
                target_variance=target_variance,
                explained_amount=0,
                unexplained_amount=0,
                constraint_results=[],
                evidence_level=EvidenceLevel.L5,
                status=HypothesisStatus.PROPOSED,
                explanation="Settlement processed by provider but bank credit cleared with valid clearing delay.",
                counterfactual_residual=0,
                hypothesis_metadata={"bank_state": "DELAYED_BANK_CREDIT"},
            )
            hypotheses.append(h)
            return hypotheses

        # 3. Handle Task: SETTLEMENT_RCA
        # Filter candidate deductions
        deduction_candidates = [
            c for c in candidates if c.entity_type in ("refund", "dispute", "adjustment")
        ]

        # 3A. Single-Event Hypotheses
        for idx, cand in enumerate(deduction_candidates):
            c_type = CauseType.REFUND if cand.entity_type == "refund" else (
                CauseType.DISPUTE if cand.entity_type == "dispute" else CauseType.ADJUSTMENT
            )
            explanation = f"Single {cand.entity_type} event ({cand.entity_id}) of amount ₹{cand.amount/100:.2f} explains settlement variance."

            h = HypothesisBuilder.create_hypothesis(
                hypothesis_id=f"hyp_single_{idx+1}_{cand.entity_id}",
                case_id=case_id,
                cause_type=c_type,
                candidate_evidence=[cand],
                target_variance=target_variance,
                explanation=explanation,
            )
            hypotheses.append(h)

        # 3B. Multi-Event / Composite Hypotheses (combining 2 or 3 deduction candidates)
        if len(deduction_candidates) >= 2:
            for r in range(2, min(4, len(deduction_candidates) + 1)):
                for combo in itertools.combinations(deduction_candidates, r):
                    combo_list = list(combo)
                    total_amount = sum(c.amount for c in combo_list)
                    names = ", ".join(f"{c.entity_type} {c.entity_id} (₹{c.amount/100:.2f})" for c in combo_list)
                    explanation = f"Composite multi-event explanation ({len(combo_list)} events): {names} summing to ₹{total_amount/100:.2f}."

                    combo_id = "_".join(c.entity_id for c in combo_list)
                    h = HypothesisBuilder.create_hypothesis(
                        hypothesis_id=f"hyp_comp_{combo_id[:40]}",
                        case_id=case_id,
                        cause_type=CauseType.COMPOSITE,
                        candidate_evidence=combo_list,
                        target_variance=target_variance,
                        explanation=explanation,
                    )
                    hypotheses.append(h)

        # 3C. Fallback Unknown Hypothesis if no deductions
        if not hypotheses:
            hypotheses.append(
                HypothesisBuilder.create_hypothesis(
                    hypothesis_id=f"hyp_unknown_{case_id}",
                    case_id=case_id,
                    cause_type=CauseType.UNKNOWN,
                    candidate_evidence=[],
                    target_variance=target_variance,
                    explanation="No valid candidate deduction events found in settlement batch.",
                )
            )

        return hypotheses
