import time
from typing import Any, List

from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.models.base import SourceEventType
from neofinesse.retrieval.base import (
    BaseRetrievalStrategy,
    EvidenceCandidate,
    InvestigationTaskCategory,
    RetrievalResult,
    RetrievalStrategy,
    TemporalRetrievalStatus,
)


class DirectIdRetrievalStrategy(BaseRetrievalStrategy):
    """Strategy 1: Direct / Identifier Retrieval using explicit deterministic keys."""

    strategy_name = RetrievalStrategy.DIRECT_ID

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

        # Find target settlement
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

        # 1. Retrieve direct constituent settlement lines by settlement_id
        target_lines = [l for l in dataset.settlement_lines if l.settlement_id == settlement_id]
        for line in target_lines:
            prov = line.provenance
            is_complete = bool(prov and prov.source_file and prov.source_row and prov.source_hash and prov.record_hash)
            candidates.append(
                EvidenceCandidate(
                    candidate_id=f"dir_line_{line.settlement_line_id}",
                    entity_type="settlement_line",
                    entity_id=line.settlement_line_id,
                    amount=line.amount,
                    net_financial_effect=line.net_amount,
                    relationship_path=f"Settlement({settlement_id}) → SettlementLine({line.settlement_line_id})",
                    temporal_status=TemporalRetrievalStatus.TEMPORALLY_VALID,
                    timestamp=line.event_timestamp or settlement.created_at,
                    provenance=prov,
                    is_provenance_complete=is_complete,
                    evidence_metadata={
                        "source_event_type": line.source_event_type.value,
                        "source_event_id": line.source_event_id,
                        "payment_id": line.payment_id,
                    },
                )
            )

            # 2. Retrieve the explicit source entity by primary key (source_event_id)
            if line.source_event_type == SourceEventType.PAYMENT:
                p = next((x for x in dataset.payments if x.id == line.source_event_id), None)
                if p:
                    p_prov = p.provenance
                    p_complete = bool(p_prov and p_prov.source_file and p_prov.source_row and p_prov.source_hash and p_prov.record_hash)
                    candidates.append(
                        EvidenceCandidate(
                            candidate_id=f"dir_pay_{p.id}",
                            entity_type="payment",
                            entity_id=p.id,
                            amount=p.amount,
                            net_financial_effect=line.net_amount,
                            relationship_path=f"SettlementLine({line.settlement_line_id}) → Payment({p.id})",
                            temporal_status=TemporalRetrievalStatus.TEMPORALLY_VALID,
                            timestamp=p.captured_at or p.created_at,
                            provenance=p_prov,
                            is_provenance_complete=p_complete,
                            evidence_metadata={"status": p.status, "method": p.method},
                        )
                    )
            elif line.source_event_type == SourceEventType.REFUND:
                r = next((x for x in dataset.refunds if x.id == line.source_event_id), None)
                if r:
                    r_prov = r.provenance
                    r_complete = bool(r_prov and r_prov.source_file and r_prov.source_row and r_prov.source_hash and r_prov.record_hash)
                    candidates.append(
                        EvidenceCandidate(
                            candidate_id=f"dir_rfnd_{r.id}",
                            entity_type="refund",
                            entity_id=r.id,
                            amount=r.amount,
                            net_financial_effect=-r.amount,
                            relationship_path=f"SettlementLine({line.settlement_line_id}) → Refund({r.id})",
                            temporal_status=TemporalRetrievalStatus.TEMPORALLY_VALID,
                            timestamp=r.processed_at or r.created_at,
                            provenance=r_prov,
                            is_provenance_complete=r_complete,
                            evidence_metadata={"status": r.status.value, "payment_id": r.payment_id},
                        )
                    )
            elif line.source_event_type == SourceEventType.ADJUSTMENT:
                a = next((x for x in dataset.adjustments if x.id == line.source_event_id), None)
                if a:
                    a_prov = a.provenance
                    a_complete = bool(a_prov and a_prov.source_file and a_prov.source_row and a_prov.source_hash and a_prov.record_hash)
                    candidates.append(
                        EvidenceCandidate(
                            candidate_id=f"dir_adj_{a.id}",
                            entity_type="adjustment",
                            entity_id=a.id,
                            amount=abs(a.amount),
                            net_financial_effect=a.amount,
                            relationship_path=f"SettlementLine({line.settlement_line_id}) → Adjustment({a.id})",
                            temporal_status=TemporalRetrievalStatus.TEMPORALLY_VALID,
                            timestamp=a.created_at,
                            provenance=a_prov,
                            is_provenance_complete=a_complete,
                            evidence_metadata={"adjustment_type": a.adjustment_type.value},
                        )
                    )
            elif line.source_event_type in (SourceEventType.DISPUTE, SourceEventType.DISPUTE_REVERSAL):
                d = next((x for x in dataset.disputes if x.id == line.source_event_id), None)
                if d:
                    d_prov = d.provenance
                    d_complete = bool(d_prov and d_prov.source_file and d_prov.source_row and d_prov.source_hash and d_prov.record_hash)
                    candidates.append(
                        EvidenceCandidate(
                            candidate_id=f"dir_disp_{d.id}",
                            entity_type="dispute",
                            entity_id=d.id,
                            amount=d.amount_deducted,
                            net_financial_effect=-d.amount_deducted,
                            relationship_path=f"SettlementLine({line.settlement_line_id}) → Dispute({d.id})",
                            temporal_status=TemporalRetrievalStatus.TEMPORALLY_VALID,
                            timestamp=d.created_at,
                            provenance=d_prov,
                            is_provenance_complete=d_complete,
                            evidence_metadata={"status": d.status.value, "phase": d.phase.value},
                        )
                    )

        # 3. Retrieve bank transaction by direct UTR
        if settlement.utr:
            b_txn = next((b for b in dataset.bank_transactions if (b.parsed_utr or b.utr or "").strip().upper() == settlement.utr.strip().upper()), None)
            if b_txn:
                b_prov = b_txn.provenance
                b_complete = bool(b_prov and b_prov.source_file and b_prov.source_row and b_prov.source_hash and b_prov.record_hash)
                candidates.append(
                    EvidenceCandidate(
                        candidate_id=f"dir_bank_{b_txn.bank_txn_id}",
                        entity_type="bank_transaction",
                        entity_id=b_txn.bank_txn_id,
                        amount=b_txn.credit_amount or 0,
                        net_financial_effect=b_txn.credit_amount,
                        relationship_path=f"Settlement({settlement_id}).utr == BankTransaction({b_txn.bank_txn_id}).utr",
                        temporal_status=TemporalRetrievalStatus.TEMPORALLY_VALID,
                        timestamp=b_txn.value_date,
                        provenance=b_prov,
                        is_provenance_complete=b_complete,
                        evidence_metadata={"utr": settlement.utr},
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
                "direct_key_count": len(target_lines) + 1,
                "target_line_count": len(target_lines),
            },
        )
