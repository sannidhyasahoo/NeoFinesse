from typing import Dict, List, Optional, Tuple

from neofinesse.ai_investigation.evidence_pack import EvidenceItem, EvidencePack
from neofinesse.ai_investigation.models import AIHypothesis, AIInvestigationResponse, AIRejectionReason


class AIResponseValidator:
    """Strict independent validator for LLM-proposed hypotheses."""

    @staticmethod
    def validate_evidence_ids(ai_hyp: AIHypothesis, pack: EvidencePack) -> Tuple[bool, List[str]]:
        """Verifies that every referenced evidence ID exists in the supplied Evidence Pack."""
        valid_ev_ids = {item.evidence_id for item in pack.evidence_items}
        invalid_ids = [ev_id for ev_id in ai_hyp.evidence_ids if ev_id not in valid_ev_ids]
        return len(invalid_ids) == 0, invalid_ids

    @staticmethod
    def recalculate_arithmetic(ai_hyp: AIHypothesis, pack: EvidencePack) -> Tuple[int, bool]:
        """Independently calculates total net financial effect from authentic evidence records."""
        ev_map: Dict[str, EvidenceItem] = {item.evidence_id: item for item in pack.evidence_items}

        total_recalculated = 0
        for ev_id in ai_hyp.evidence_ids:
            if ev_id in ev_map:
                total_recalculated += ev_map[ev_id].net_financial_effect_paise

        is_match = (total_recalculated == ai_hyp.claimed_explained_amount)
        return total_recalculated, is_match

    @classmethod
    def validate_hypotheses(
        cls, response: AIInvestigationResponse, pack: EvidencePack
    ) -> Tuple[List[AIHypothesis], List[AIRejectionReason]]:
        """Validates all hypotheses in the AI response and calculates independent arithmetic."""
        validated: List[AIHypothesis] = []
        rejections: List[AIRejectionReason] = []

        for hyp in response.hypotheses:
            # 1. Check for hallucinated evidence IDs
            ids_valid, invalid_ids = cls.validate_evidence_ids(hyp, pack)
            if not ids_valid:
                rejections.append(
                    AIRejectionReason(
                        hypothesis_id=hyp.hypothesis_id,
                        rejection_stage="HALLUCINATION_CHECK",
                        reasons=[f"Referenced non-existent evidence IDs: {invalid_ids}"],
                    )
                )
                continue

            # 2. Independent arithmetic recalculation
            recalc_amount, arithmetic_matched = cls.recalculate_arithmetic(hyp, pack)
            hyp.recalculated_explained_amount = recalc_amount

            # If arithmetic mismatch occurred, we keep the hypothesis but override with true calculated amount
            if not arithmetic_matched:
                hyp.assumptions.append(
                    f"Arithmetic corrected independently: claimed {hyp.claimed_explained_amount} paise, actual {recalc_amount} paise."
                )

            validated.append(hyp)

        return validated, rejections
