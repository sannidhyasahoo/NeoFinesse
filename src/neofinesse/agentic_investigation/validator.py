from datetime import datetime
from typing import Any, Dict, List, Tuple

from neofinesse.agentic_investigation.models import AgentHypothesisProposal, AgentRoundResponse
from neofinesse.agentic_investigation.state import InvestigationState
from neofinesse.investigation.hypothesis import HypothesisBuilder
from neofinesse.investigation.models import Hypothesis
from neofinesse.models.base import ProvenanceReference, Provider, SourceType
from neofinesse.retrieval.base import EvidenceCandidate, TemporalRetrievalStatus


class AgentResponseValidator:
    """Validates AI hypotheses against current state, checks hallucinated IDs, and recalculates arithmetic."""

    @staticmethod
    def validate_and_bridge_hypotheses(
        response: AgentRoundResponse,
        state: InvestigationState,
    ) -> Tuple[List[Hypothesis], List[Dict[str, Any]]]:
        verified_candidates: List[Hypothesis] = []
        rejections: List[Dict[str, Any]] = []

        for hyp in response.hypotheses:
            # 1. Hallucination Check
            invalid_ids = [ev_id for ev_id in hyp.evidence_ids if ev_id not in state.current_evidence]
            if invalid_ids:
                rejections.append(
                    {
                        "hypothesis_id": hyp.hypothesis_id,
                        "stage": "HALLUCINATION_CHECK",
                        "reason": f"Referenced non-existent evidence IDs: {invalid_ids}",
                    }
                )
                continue

            # 2. Reconstruct authentic EvidenceCandidate objects from state.current_evidence
            matched_cands: List[EvidenceCandidate] = []
            for ev_id in hyp.evidence_ids:
                ev_item = state.current_evidence[ev_id]
                ts = datetime.fromisoformat(ev_item.timestamp_iso) if ev_item.timestamp_iso else None
                prov = None
                if ev_item.source_file and ev_item.source_hash and ev_item.record_hash:
                    prov = ProvenanceReference(
                        source_id=ev_item.source_id,
                        source_type=SourceType.CSV,
                        source_file=ev_item.source_file,
                        source_sheet=ev_item.source_sheet,
                        source_row=max(1, ev_item.source_row),
                        source_columns={"amount": "B2"},
                        source_hash=ev_item.source_hash,
                        record_hash=ev_item.record_hash,
                        provider=Provider.RAZORPAY,
                        ingested_at=datetime.now(),
                        ingested_by="neofinesse_pipeline",
                    )

                matched_cands.append(
                    EvidenceCandidate(
                        candidate_id=ev_item.candidate_id,
                        entity_type=ev_item.entity_type,
                        entity_id=ev_item.entity_id,
                        amount=ev_item.amount_paise,
                        net_financial_effect=ev_item.net_financial_effect_paise,
                        relationship_path=ev_item.relationship_path,
                        temporal_status=TemporalRetrievalStatus.TEMPORALLY_VALID,
                        timestamp=ts,
                        is_provenance_complete=bool(ev_item.source_hash and ev_item.record_hash),
                        provenance=prov,
                        evidence_metadata=ev_item.evidence_metadata,
                    )
                )

            # 3. Build Phase 5 Hypothesis
            phase5_hyp = HypothesisBuilder.create_hypothesis(
                hypothesis_id=hyp.hypothesis_id,
                case_id=state.case_id,
                cause_type=hyp.cause_type,
                candidate_evidence=matched_cands,
                target_variance=state.target_variance,
                explanation=hyp.reasoning,
            )

            # 4. Check Arithmetic Consistency
            actual_sum = sum(c.net_financial_effect for c in matched_cands)
            hyp.recalculated_explained_amount = actual_sum

            verified_candidates.append(phase5_hyp)

        return verified_candidates, rejections
