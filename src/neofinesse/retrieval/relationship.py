import time
from typing import List

from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.models.base import SourceEventType
from neofinesse.retrieval.base import (
    BaseRetrievalStrategy,
    EvidenceCandidate,
    RejectedEvidenceCandidate,
    RetrievalResult,
    RetrievalStrategy,
    TemporalRetrievalStatus,
)


class RelationshipAwareRetrievalStrategy(BaseRetrievalStrategy):
    """Strategy 3: Relationship-Aware Retrieval traversing explicit financial foreign-key paths."""

    strategy_name = RetrievalStrategy.RELATIONSHIP

    def retrieve(
        self, case_id: str, settlement_id: str, target_variance: int, dataset: IngestedDataset
    ) -> RetrievalResult:
        start_time = time.perf_counter()
        candidates: List[EvidenceCandidate] = []
        rejected: List[RejectedEvidenceCandidate] = []

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
                retrieval_latency_ms=latency,
                retrieval_metadata={"error": "Settlement not found"},
            )

        # 1. Direct SettlementLines in batch
        target_lines = [l for l in dataset.settlement_lines if l.settlement_id == settlement_id]
        batch_line_ids = {l.settlement_line_id for l in target_lines}
        batch_source_event_ids = {l.source_event_id for l in target_lines}
        batch_payment_ids = {l.source_event_id for l in target_lines if l.source_event_type == SourceEventType.PAYMENT}

        # Index maps
        refund_by_id = {r.id: r for r in dataset.refunds}
        dispute_by_id = {d.id: d for d in dataset.disputes}
        adjustment_by_id = {a.id: a for a in dataset.adjustments}
        payment_by_id = {p.id: p for p in dataset.payments}
        upi_by_payment = {u.payment_id: u for u in dataset.upi_transactions}

        # Traverse SettlementLines
        for line in target_lines:
            prov = line.provenance
            is_comp = bool(prov and prov.source_file and prov.source_row and prov.source_hash and prov.record_hash)

            if line.source_event_type == SourceEventType.REFUND:
                r = refund_by_id.get(line.source_event_id)
                r_prov = r.provenance if r else prov
                r_comp = bool(r_prov and r_prov.source_file and r_prov.source_row and r_prov.source_hash and r_prov.record_hash)
                candidates.append(
                    EvidenceCandidate(
                        candidate_id=f"rel_rfnd_{line.source_event_id}",
                        entity_type="refund",
                        entity_id=line.source_event_id,
                        amount=line.amount,
                        net_financial_effect=line.net_amount,
                        relationship_path=f"Settlement({settlement_id}) → SettlementLine({line.settlement_line_id}) → Refund({line.source_event_id})",
                        temporal_status=TemporalRetrievalStatus.NOT_EVALUATED,
                        timestamp=line.event_timestamp or settlement.created_at,
                        provenance=r_prov,
                        is_provenance_complete=r_comp,
                        evidence_metadata={"settlement_line_id": line.settlement_line_id, "payment_id": line.payment_id},
                    )
                )
            elif line.source_event_type == SourceEventType.ADJUSTMENT:
                a = adjustment_by_id.get(line.source_event_id)
                a_prov = a.provenance if a else prov
                a_comp = bool(a_prov and a_prov.source_file and a_prov.source_row and a_prov.source_hash and a_prov.record_hash)
                candidates.append(
                    EvidenceCandidate(
                        candidate_id=f"rel_adj_{line.source_event_id}",
                        entity_type="adjustment",
                        entity_id=line.source_event_id,
                        amount=abs(line.amount),
                        net_financial_effect=line.net_amount,
                        relationship_path=f"Settlement({settlement_id}) → SettlementLine({line.settlement_line_id}) → Adjustment({line.source_event_id})",
                        temporal_status=TemporalRetrievalStatus.NOT_EVALUATED,
                        timestamp=line.event_timestamp or settlement.created_at,
                        provenance=a_prov,
                        is_provenance_complete=a_comp,
                        evidence_metadata={"settlement_line_id": line.settlement_line_id},
                    )
                )
            elif line.source_event_type in (SourceEventType.DISPUTE, SourceEventType.DISPUTE_REVERSAL):
                d = dispute_by_id.get(line.source_event_id)
                d_prov = d.provenance if d else prov
                d_comp = bool(d_prov and d_prov.source_file and d_prov.source_row and d_prov.source_hash and d_prov.record_hash)
                candidates.append(
                    EvidenceCandidate(
                        candidate_id=f"rel_disp_{line.source_event_id}",
                        entity_type="dispute",
                        entity_id=line.source_event_id,
                        amount=line.amount,
                        net_financial_effect=line.net_amount,
                        relationship_path=f"Settlement({settlement_id}) → SettlementLine({line.settlement_line_id}) → Dispute({line.source_event_id})",
                        temporal_status=TemporalRetrievalStatus.NOT_EVALUATED,
                        timestamp=line.event_timestamp or settlement.created_at,
                        provenance=d_prov,
                        is_provenance_complete=d_comp,
                        evidence_metadata={"settlement_line_id": line.settlement_line_id, "payment_id": line.payment_id},
                    )
                )
            elif line.source_event_type == SourceEventType.PAYMENT:
                p = payment_by_id.get(line.source_event_id)
                p_prov = p.provenance if p else prov
                p_comp = bool(p_prov and p_prov.source_file and p_prov.source_row and p_prov.source_hash and p_prov.record_hash)
                candidates.append(
                    EvidenceCandidate(
                        candidate_id=f"rel_pay_{line.source_event_id}",
                        entity_type="payment",
                        entity_id=line.source_event_id,
                        amount=line.amount,
                        net_financial_effect=line.net_amount,
                        relationship_path=f"Settlement({settlement_id}) → SettlementLine({line.settlement_line_id}) → Payment({line.source_event_id})",
                        temporal_status=TemporalRetrievalStatus.NOT_EVALUATED,
                        timestamp=line.event_timestamp or settlement.created_at,
                        provenance=p_prov,
                        is_provenance_complete=p_comp,
                        evidence_metadata={"settlement_line_id": line.settlement_line_id},
                    )
                )

        # 2. Traverse Payment → Linked Events not in lines yet
        for p_id in batch_payment_ids:
            # Check linked refunds
            for r in dataset.refunds:
                if r.payment_id == p_id and r.id not in batch_source_event_ids:
                    r_prov = r.provenance
                    r_comp = bool(r_prov and r_prov.source_file and r_prov.source_row and r_prov.source_hash and r_prov.record_hash)
                    candidates.append(
                        EvidenceCandidate(
                            candidate_id=f"rel_pay_rfnd_{r.id}",
                            entity_type="refund",
                            entity_id=r.id,
                            amount=r.amount,
                            net_financial_effect=-r.amount,
                            relationship_path=f"Settlement({settlement_id}) → Payment({p_id}) → Refund({r.id})",
                            temporal_status=TemporalRetrievalStatus.NOT_EVALUATED,
                            timestamp=r.processed_at or r.created_at,
                            provenance=r_prov,
                            is_provenance_complete=r_comp,
                            evidence_metadata={"payment_id": p_id},
                        )
                    )
            # Check linked disputes
            for d in dataset.disputes:
                if d.payment_id == p_id and d.id not in batch_source_event_ids:
                    d_prov = d.provenance
                    d_comp = bool(d_prov and d_prov.source_file and d_prov.source_row and d_prov.source_hash and d_prov.record_hash)
                    candidates.append(
                        EvidenceCandidate(
                            candidate_id=f"rel_pay_disp_{d.id}",
                            entity_type="dispute",
                            entity_id=d.id,
                            amount=d.amount_deducted,
                            net_financial_effect=-d.amount_deducted,
                            relationship_path=f"Settlement({settlement_id}) → Payment({p_id}) → Dispute({d.id})",
                            temporal_status=TemporalRetrievalStatus.NOT_EVALUATED,
                            timestamp=d.created_at,
                            provenance=d_prov,
                            is_provenance_complete=d_comp,
                            evidence_metadata={"payment_id": p_id},
                        )
                    )

        # 3. Explicitly evaluate and record rejected decoys (e.g. wrong-settlement or wrong-payment decoys)
        target_abs = abs(target_variance)
        if target_abs > 0:
            for r in dataset.refunds:
                if r.amount == target_abs and r.id not in batch_source_event_ids and r.payment_id not in batch_payment_ids and r.settlement_id != settlement_id:
                    rejected.append(
                        RejectedEvidenceCandidate(
                            candidate_id=f"rej_decoy_rfnd_{r.id}",
                            entity_type="refund",
                            entity_id=r.id,
                            amount=r.amount,
                            rejection_strategy=self.strategy_name,
                            rejection_reason=f"Decoy refund belongs to unrelated settlement ({r.settlement_id}) and payment ({r.payment_id}).",
                            relationship_path=f"Unrelated Settlement({r.settlement_id}) → Payment({r.payment_id}) → Refund({r.id})",
                            timestamp=r.processed_at or r.created_at,
                            provenance=r.provenance,
                        )
                    )
            for d in dataset.disputes:
                if d.amount_deducted == target_abs and d.id not in batch_source_event_ids and d.payment_id not in batch_payment_ids and d.settlement_id != settlement_id:
                    rejected.append(
                        RejectedEvidenceCandidate(
                            candidate_id=f"rej_decoy_disp_{d.id}",
                            entity_type="dispute",
                            entity_id=d.id,
                            amount=d.amount_deducted,
                            rejection_strategy=self.strategy_name,
                            rejection_reason=f"Decoy dispute belongs to unrelated payment ({d.payment_id}) in another settlement ({d.settlement_id}).",
                            relationship_path=f"Unrelated Settlement({d.settlement_id}) → Payment({d.payment_id}) → Dispute({d.id})",
                            timestamp=d.created_at,
                            provenance=d.provenance,
                        )
                    )

        latency = (time.perf_counter() - start_time) * 1000.0
        return RetrievalResult(
            case_id=case_id,
            settlement_id=settlement_id,
            strategy=self.strategy_name,
            target_variance=target_variance,
            candidates=candidates,
            rejected_candidates=rejected,
            retrieval_latency_ms=latency,
            retrieval_metadata={
                "batch_line_count": len(target_lines),
                "batch_payment_count": len(batch_payment_ids),
                "rejected_decoy_count": len(rejected),
            },
        )
