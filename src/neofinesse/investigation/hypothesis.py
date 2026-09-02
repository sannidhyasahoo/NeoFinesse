from typing import List, Optional

from neofinesse.investigation.models import CauseType, Hypothesis, HypothesisStatus
from neofinesse.models.base import EvidenceLevel
from neofinesse.retrieval.base import EvidenceCandidate


class HypothesisBuilder:
    """Utility to construct candidate hypotheses and perform counterfactual calculations."""

    @staticmethod
    def create_hypothesis(
        hypothesis_id: str,
        case_id: str,
        cause_type: CauseType,
        candidate_evidence: List[EvidenceCandidate],
        target_variance: int,
        explanation: str,
    ) -> Hypothesis:
        # Calculate proposed explained amount as the signed sum of financial effects
        # Financial effect: negative reduces settlement, positive increases
        total_effect = 0
        for cand in candidate_evidence:
            if cand.net_financial_effect is not None:
                total_effect += cand.net_financial_effect
            else:
                # Default sign convention: refunds/disputes/adjustments are negative deductions
                if cand.entity_type in ("refund", "dispute", "adjustment"):
                    total_effect -= abs(cand.amount)
                else:
                    total_effect += abs(cand.amount)

        # Variance is: target_variance (e.g. -200000 paise)
        # explained amount matches the target variance direction
        explained = total_effect
        unexplained = target_variance - explained

        evidence_ids = [c.entity_id for c in candidate_evidence]

        return Hypothesis(
            hypothesis_id=hypothesis_id,
            case_id=case_id,
            cause_type=cause_type,
            evidence_ids=evidence_ids,
            candidate_evidence=candidate_evidence,
            target_variance=target_variance,
            explained_amount=explained,
            unexplained_amount=unexplained,
            constraint_results=[],
            evidence_level=EvidenceLevel.L0,
            status=HypothesisStatus.PROPOSED,
            explanation=explanation,
            counterfactual_residual=None,
            hypothesis_metadata={},
        )

    @staticmethod
    def compute_counterfactual_residual(
        hypothesis: Hypothesis, excluded_candidate_id: Optional[str] = None
    ) -> int:
        """Calculates what the residual unexplained variance would be if a specific evidence item was removed."""
        target = hypothesis.target_variance
        retained_effect = 0

        for cand in hypothesis.candidate_evidence:
            if excluded_candidate_id and cand.entity_id == excluded_candidate_id:
                continue  # simulate removing this candidate

            if cand.net_financial_effect is not None:
                retained_effect += cand.net_financial_effect
            else:
                if cand.entity_type in ("refund", "dispute", "adjustment"):
                    retained_effect -= abs(cand.amount)
                else:
                    retained_effect += abs(cand.amount)

        # Residual variance without the excluded candidate
        residual = target - retained_effect
        return residual
