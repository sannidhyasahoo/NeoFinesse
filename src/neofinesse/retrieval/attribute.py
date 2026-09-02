import time
from typing import List

from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.retrieval.base import (
    BaseRetrievalStrategy,
    EvidenceCandidate,
    InvestigationTaskCategory,
    RetrievalResult,
    RetrievalStrategy,
    TemporalRetrievalStatus,
)


class AttributeRetrievalStrategy(BaseRetrievalStrategy):
    """Strategy 2: Attribute Retrieval matching candidates globally by amount and transaction type."""

    strategy_name = RetrievalStrategy.ATTRIBUTE

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

        candidates: List[EvidenceCandidate] = []
        target_abs = abs(target_variance)

        if target_abs == 0:
            # For zero variance cases, retrieve matching amount components
            target_abs = 0

        # Global scan of Refunds matching target amount
        for r in dataset.refunds:
            if target_abs > 0 and r.amount == target_abs:
                prov = r.provenance
                is_comp = bool(prov and prov.source_file and prov.source_row and prov.source_hash and prov.record_hash)
                # Note: this will intentionally capture same-amount decoys across the entire world
                is_unrelated = (r.settlement_id != settlement_id)
                candidates.append(
                    EvidenceCandidate(
                        candidate_id=f"attr_rfnd_{r.id}",
                        entity_type="refund",
                        entity_id=r.id,
                        amount=r.amount,
                        net_financial_effect=-r.amount,
                        relationship_path=f"AmountMatch(amount={r.amount}) → Refund({r.id})",
                        temporal_status=TemporalRetrievalStatus.NOT_EVALUATED,
                        timestamp=r.processed_at or r.created_at,
                        provenance=prov,
                        is_provenance_complete=is_comp,
                        is_decoy=is_unrelated,
                        evidence_metadata={
                            "matched_attribute": "amount",
                            "settlement_id": r.settlement_id,
                            "payment_id": r.payment_id,
                        },
                    )
                )

        # Global scan of Disputes matching target amount
        for d in dataset.disputes:
            if target_abs > 0 and (d.amount == target_abs or d.amount_deducted == target_abs):
                prov = d.provenance
                is_comp = bool(prov and prov.source_file and prov.source_row and prov.source_hash and prov.record_hash)
                is_unrelated = (d.settlement_id != settlement_id)
                candidates.append(
                    EvidenceCandidate(
                        candidate_id=f"attr_disp_{d.id}",
                        entity_type="dispute",
                        entity_id=d.id,
                        amount=d.amount_deducted,
                        net_financial_effect=-d.amount_deducted,
                        relationship_path=f"AmountMatch(amount={d.amount_deducted}) → Dispute({d.id})",
                        temporal_status=TemporalRetrievalStatus.NOT_EVALUATED,
                        timestamp=d.created_at,
                        provenance=prov,
                        is_provenance_complete=is_comp,
                        is_decoy=is_unrelated,
                        evidence_metadata={
                            "matched_attribute": "amount",
                            "settlement_id": d.settlement_id,
                            "payment_id": d.payment_id,
                        },
                    )
                )

        # Global scan of Adjustments matching target amount
        for a in dataset.adjustments:
            if target_abs > 0 and (abs(a.amount) == target_abs or a.amount == target_variance):
                prov = a.provenance
                is_comp = bool(prov and prov.source_file and prov.source_row and prov.source_hash and prov.record_hash)
                is_unrelated = (a.settlement_id != settlement_id)
                candidates.append(
                    EvidenceCandidate(
                        candidate_id=f"attr_adj_{a.id}",
                        entity_type="adjustment",
                        entity_id=a.id,
                        amount=abs(a.amount),
                        net_financial_effect=a.amount,
                        relationship_path=f"AmountMatch(amount={abs(a.amount)}) → Adjustment({a.id})",
                        temporal_status=TemporalRetrievalStatus.NOT_EVALUATED,
                        timestamp=a.created_at,
                        provenance=prov,
                        is_provenance_complete=is_comp,
                        is_decoy=is_unrelated,
                        evidence_metadata={
                            "matched_attribute": "amount",
                            "settlement_id": a.settlement_id,
                        },
                    )
                )

        # Global scan of Payments matching target amount
        for p in dataset.payments:
            if target_abs > 0 and (p.amount == target_abs or abs(p.net_amount) == target_abs):
                prov = p.provenance
                is_comp = bool(prov and prov.source_file and prov.source_row and prov.source_hash and prov.record_hash)
                is_unrelated = (p.settlement_id != settlement_id)
                candidates.append(
                    EvidenceCandidate(
                        candidate_id=f"attr_pay_{p.id}",
                        entity_type="payment",
                        entity_id=p.id,
                        amount=p.amount,
                        net_financial_effect=p.net_amount,
                        relationship_path=f"AmountMatch(amount={p.amount}) → Payment({p.id})",
                        temporal_status=TemporalRetrievalStatus.NOT_EVALUATED,
                        timestamp=p.captured_at or p.created_at,
                        provenance=prov,
                        is_provenance_complete=is_comp,
                        is_decoy=is_unrelated,
                        evidence_metadata={
                            "matched_attribute": "amount",
                            "settlement_id": p.settlement_id,
                        },
                    )
                )

        latency = (time.perf_counter() - start_time) * 1000.0
        return RetrievalResult(
            case_id=case_id,
            settlement_id=settlement_id,
            strategy=self.strategy_name,
            target_variance=target_variance,
            candidates=candidates,
            rejected_candidates=[],
            retrieval_latency_ms=latency,
            retrieval_metadata={
                "matched_attribute": "amount",
                "target_amount_paise": target_abs,
                "global_candidate_count": len(candidates),
            },
        )
