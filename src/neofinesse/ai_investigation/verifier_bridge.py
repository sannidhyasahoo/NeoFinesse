from typing import Dict, List, Optional, Tuple

from neofinesse.ai_investigation.evidence_pack import EvidenceItem, EvidencePack
from neofinesse.ai_investigation.models import AIHypothesis, AIRejectionReason
from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.investigation.hypothesis import HypothesisBuilder
from neofinesse.investigation.models import ConstraintStatus, Hypothesis, HypothesisStatus
from neofinesse.investigation.verifier import HypothesisVerifier
from neofinesse.retrieval.base import EvidenceCandidate, RetrievalResult


class AIVerifierBridge:
    """Bridges validated AI hypotheses directly to Phase 5 deterministic constraint verification."""

    @staticmethod
    def bridge_to_phase5_hypothesis(
        ai_hyp: AIHypothesis,
        pack: EvidencePack,
        retrieval_result: RetrievalResult,
        target_variance: int,
    ) -> Hypothesis:
        # Build mapping from evidence_id (EV-1) to original EvidenceCandidate
        ev_id_to_cand_id = {item.evidence_id: item.candidate_id for item in pack.evidence_items}
        cand_map: Dict[str, EvidenceCandidate] = {c.candidate_id: c for c in retrieval_result.candidates}

        matched_candidates: List[EvidenceCandidate] = []
        for ev_id in ai_hyp.evidence_ids:
            cand_id = ev_id_to_cand_id.get(ev_id)
            if cand_id and cand_id in cand_map:
                matched_candidates.append(cand_map[cand_id])

        # Construct Phase 5 hypothesis using builder
        phase5_hyp = HypothesisBuilder.create_hypothesis(
            hypothesis_id=ai_hyp.hypothesis_id,
            case_id=pack.case_id,
            cause_type=ai_hyp.cause_type,
            candidate_evidence=matched_candidates,
            target_variance=target_variance,
            explanation=ai_hyp.reasoning,
        )

        return phase5_hyp

    @classmethod
    def verify_ai_hypotheses(
        cls,
        ai_hypotheses: List[AIHypothesis],
        pack: EvidencePack,
        retrieval_result: RetrievalResult,
        settlement_id: str,
        target_variance: int,
        dataset: IngestedDataset,
    ) -> Tuple[List[Hypothesis], List[AIRejectionReason]]:
        """Verifies each AI hypothesis against Phase 5 deterministic constraints."""
        verified_hypotheses: List[Hypothesis] = []
        rejections: List[AIRejectionReason] = []

        for ai_hyp in ai_hypotheses:
            phase5_hyp = cls.bridge_to_phase5_hypothesis(
                ai_hyp=ai_hyp,
                pack=pack,
                retrieval_result=retrieval_result,
                target_variance=target_variance,
            )

            # Execute Phase 5 verification
            verified_hyp = HypothesisVerifier.verify(
                hypothesis=phase5_hyp,
                settlement_id=settlement_id,
                target_variance=target_variance,
                dataset=dataset,
            )

            if verified_hyp.status in (HypothesisStatus.VERIFIED, HypothesisStatus.PARTIALLY_VERIFIED):
                verified_hypotheses.append(verified_hyp)
            else:
                failed_reasons = [
                    f"{cr.constraint_name}: {cr.reason}"
                    for cr in verified_hyp.constraint_results
                    if cr.status == ConstraintStatus.FAIL
                ]
                rejections.append(
                    AIRejectionReason(
                        hypothesis_id=ai_hyp.hypothesis_id,
                        rejection_stage="VERIFIER_CONSTRAINTS",
                        reasons=failed_reasons,
                    )
                )

        return verified_hypotheses, rejections
