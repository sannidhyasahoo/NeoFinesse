import time
from typing import List

from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.reconciliation.temporal import TemporalConstraintFilter, TemporalStatus
from neofinesse.retrieval.base import (
    BaseRetrievalStrategy,
    EvidenceCandidate,
    InvestigationTaskCategory,
    RejectedEvidenceCandidate,
    RetrievalResult,
    RetrievalStrategy,
    TemporalRetrievalStatus,
)
from neofinesse.retrieval.relationship import RelationshipAwareRetrievalStrategy


class TemporalRelationshipRetrievalStrategy(BaseRetrievalStrategy):
    """Strategy 5: Temporal-Aware Retrieval applying strict temporal window validation to relational candidates."""

    strategy_name = RetrievalStrategy.TEMPORAL_RELATIONSHIP

    def __init__(self, allowable_lead_buffer_hours: float = 2.0):
        self._rel_strategy = RelationshipAwareRetrievalStrategy()
        self.temporal_filter = TemporalConstraintFilter(allowable_lead_buffer_hours=allowable_lead_buffer_hours)

    def retrieve(
        self,
        case_id: str,
        settlement_id: str,
        target_variance: int,
        dataset: IngestedDataset,
        task_category: InvestigationTaskCategory = InvestigationTaskCategory.SETTLEMENT_RCA,
    ) -> RetrievalResult:
        start_time = time.perf_counter()

        if not self.is_strategy_applicable(task_category):
            latency = (time.perf_counter() - start_time) * 1000.0
            return RetrievalResult(
                case_id=case_id,
                settlement_id=settlement_id,
                strategy=self.strategy_name,
                target_variance=target_variance,
                candidates=[],
                rejected_candidates=[],
                is_applicable=False,
                retrieval_latency_ms=latency,
                retrieval_metadata={"status": "NOT_APPLICABLE_FOR_TASK", "task_category": task_category.value},
            )

        settlement = next((s for s in dataset.settlements if s.id == settlement_id), None)
        if not settlement:
            latency = (time.perf_counter() - start_time) * 1000.0
            return RetrievalResult(
                case_id=case_id,
                settlement_id=settlement_id,
                strategy=self.strategy_name,
                target_variance=target_variance,
                candidates=[],
                rejected_candidates=[],
                is_applicable=True,
                retrieval_latency_ms=latency,
                retrieval_metadata={"error": "Settlement not found"},
            )

        # 1. Retrieve base relationship candidates
        base_result = self._rel_strategy.retrieve(case_id, settlement_id, target_variance, dataset, task_category)

        valid_candidates: List[EvidenceCandidate] = []
        rejected_candidates: List[RejectedEvidenceCandidate] = list(base_result.rejected_candidates)

        # 2. Also check global candidates for wrong-date decoys (e.g. VAR-008 where decoy is associated with batch payment but occurs 20 days later)
        target_abs = abs(target_variance)
        if target_abs > 0:
            for r in dataset.refunds:
                if r.amount == target_abs and r.settlement_id == settlement_id:
                    # Check if already in candidates
                    if not any(c.entity_id == r.id for c in base_result.candidates):
                        base_result.candidates.append(
                            EvidenceCandidate(
                                candidate_id=f"temp_rfnd_{r.id}",
                                entity_type="refund",
                                entity_id=r.id,
                                amount=r.amount,
                                net_financial_effect=-r.amount,
                                relationship_path=f"Settlement({settlement_id}) → Refund({r.id})",
                                temporal_status=TemporalRetrievalStatus.NOT_EVALUATED,
                                timestamp=r.processed_at or r.created_at,
                                provenance=r.provenance,
                                is_provenance_complete=bool(r.provenance and r.provenance.source_file),
                            )
                        )

        # 3. Apply temporal constraint validation
        for cand in base_result.candidates:
            if not cand.timestamp:
                rejected_candidates.append(
                    RejectedEvidenceCandidate(
                        candidate_id=cand.candidate_id,
                        entity_type=cand.entity_type,
                        entity_id=cand.entity_id,
                        amount=cand.amount,
                        rejection_strategy=self.strategy_name,
                        rejection_reason="Candidate lacks timestamp evidence.",
                        relationship_path=cand.relationship_path,
                        timestamp=None,
                        provenance=cand.provenance,
                    )
                )
                continue

            # Check timing against settlement cutoff
            settle_time = settlement.settled_at or settlement.created_at
            if not settle_time:
                valid_candidates.append(cand)
                continue

            from datetime import timedelta
            max_allowed = settle_time + timedelta(hours=self.temporal_filter.allowable_lead_buffer_hours)

            if cand.timestamp <= max_allowed:
                cand_copy = cand.model_copy(
                    update={"temporal_status": TemporalRetrievalStatus.TEMPORALLY_VALID}
                )
                valid_candidates.append(cand_copy)
            else:
                diff_days = (cand.timestamp - settle_time).total_seconds() / 86400.0
                rejected_candidates.append(
                    RejectedEvidenceCandidate(
                        candidate_id=cand.candidate_id,
                        entity_type=cand.entity_type,
                        entity_id=cand.entity_id,
                        amount=cand.amount,
                        rejection_strategy=self.strategy_name,
                        rejection_reason=f"Event timestamp {cand.timestamp.isoformat()} occurred {diff_days:.1f} days AFTER settlement cutoff ({settle_time.isoformat()}).",
                        relationship_path=cand.relationship_path,
                        timestamp=cand.timestamp,
                        provenance=cand.provenance,
                    )
                )

        latency = (time.perf_counter() - start_time) * 1000.0
        return RetrievalResult(
            case_id=case_id,
            settlement_id=settlement_id,
            strategy=self.strategy_name,
            target_variance=target_variance,
            candidates=valid_candidates,
            rejected_candidates=rejected_candidates,
            retrieval_latency_ms=latency,
            retrieval_metadata={
                "temporally_valid_count": len(valid_candidates),
                "temporally_rejected_count": len(rejected_candidates) - len(base_result.rejected_candidates),
            },
        )
