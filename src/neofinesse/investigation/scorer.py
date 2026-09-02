from typing import List, Optional

from neofinesse.investigation.models import ConstraintStatus, Hypothesis, HypothesisStatus
from neofinesse.models.base import EvidenceLevel


class HypothesisScorer:
    """Ranks hypotheses using deterministic, interpretable financial and structural criteria."""

    @staticmethod
    def rank_hypotheses(hypotheses: List[Hypothesis], target_variance: int) -> List[Hypothesis]:
        if not hypotheses:
            return []

        def sort_key(h: Hypothesis):
            # 1. Status rank (VERIFIED = 3, PARTIALLY_VERIFIED = 2, PROPOSED = 1, REJECTED = 0)
            status_order = {
                HypothesisStatus.VERIFIED: 3,
                HypothesisStatus.PARTIALLY_VERIFIED: 2,
                HypothesisStatus.PROPOSED: 1,
                HypothesisStatus.REJECTED: 0,
            }
            status_score = status_order.get(h.status, 0)

            # 2. Evidence level rank (L5 = 5 ... L0 = 0)
            lvl_order = {
                EvidenceLevel.L5: 5,
                EvidenceLevel.L4: 4,
                EvidenceLevel.L3: 3,
                EvidenceLevel.L2: 2,
                EvidenceLevel.L1: 1,
                EvidenceLevel.L0: 0,
            }
            lvl_score = lvl_order.get(h.evidence_level, 0)

            # 3. Exact monetary completeness (1 if target matches exactly, 0 otherwise)
            target_abs = abs(target_variance)
            candidate_sum = sum(c.amount for c in h.candidate_evidence)
            exact_monetary = 1 if (candidate_sum == target_abs or (target_variance == 0 and h.explained_amount == 0)) else 0

            # 4. Provenance completeness (1 if all pass, 0 otherwise)
            prov_passed = 1 if any(r.constraint_name == "ProvenanceConstraint" and r.status == ConstraintStatus.PASS for r in h.constraint_results) else 0

            # 5. Parsimony: fewer composite events preferred (negative event count)
            event_count = len(h.candidate_evidence)

            return (status_score, exact_monetary, lvl_score, prov_passed, -event_count)

        # Sort descending
        return sorted(hypotheses, key=sort_key, reverse=True)

    @staticmethod
    def select_winning_hypothesis(ranked_hypotheses: List[Hypothesis]) -> Optional[Hypothesis]:
        if not ranked_hypotheses:
            return None

        top = ranked_hypotheses[0]
        # Only hypotheses that are VERIFIED or PARTIALLY_VERIFIED can win
        if top.status in (HypothesisStatus.VERIFIED, HypothesisStatus.PARTIALLY_VERIFIED):
            return top

        return None
