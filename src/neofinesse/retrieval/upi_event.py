import time
from typing import List

from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.models.base import SourceEventType
from neofinesse.reconciliation.upi_state import UPIStateReconstructor
from neofinesse.retrieval.base import (
    BaseRetrievalStrategy,
    EvidenceCandidate,
    RetrievalResult,
    RetrievalStrategy,
    TemporalRetrievalStatus,
)


class UPIEventRetrievalStrategy(BaseRetrievalStrategy):
    """Strategy 6: UPI Event Retrieval extracting complete chronological state transitions and debit/reversal evidence."""

    strategy_name = RetrievalStrategy.UPI_EVENT

    def __init__(self):
        self.upi_reconstructor = UPIStateReconstructor()

    def retrieve(
        self, case_id: str, settlement_id: str, target_variance: int, dataset: IngestedDataset
    ) -> RetrievalResult:
        start_time = time.perf_counter()
        candidates: List[EvidenceCandidate] = []

        settlement = next((s for s in dataset.settlements if s.id == settlement_id), None)

        # 1. Identify target payment IDs associated with this settlement (or all UPI transactions if unsettled case)
        target_payment_ids = set()
        if settlement:
            target_lines = [l for l in dataset.settlement_lines if l.settlement_id == settlement_id]
            target_payment_ids = {l.source_event_id for l in target_lines if l.source_event_type == SourceEventType.PAYMENT}

        # 2. Find matching UPI transactions
        matched_upi_txns = []
        if target_payment_ids:
            matched_upi_txns = [u for u in dataset.upi_transactions if u.payment_id in target_payment_ids]
        else:
            # If no settlement or unsettled case (e.g. VAR-006 unsettled UPI debit reversal), match by amount or recent failure
            target_abs = abs(target_variance)
            matched_upi_txns = [u for u in dataset.upi_transactions if u.amount == target_abs or u.debit_observed]

        # 3. For each UPI transaction, retrieve the complete chronological event chain
        for u in matched_upi_txns:
            # Reconstruct state
            recon_state = self.upi_reconstructor.reconstruct(u, dataset.upi_events)

            u_prov = u.provenance
            u_comp = bool(u_prov and u_prov.source_file and u_prov.source_row and u_prov.source_hash and u_prov.record_hash)

            # Retrieve and sort all events for this transaction
            events = [e for e in dataset.upi_events if e.upi_transaction_id == u.upi_transaction_id]
            events.sort(key=lambda x: x.timestamp)

            event_history_payload = []
            for ev in events:
                ev_prov = ev.provenance
                ev_comp = bool(ev_prov and ev_prov.source_file and ev_prov.source_row and ev_prov.source_hash and ev_prov.record_hash)

                event_history_payload.append(
                    {
                        "event_id": ev.event_id,
                        "timestamp": ev.timestamp.isoformat(),
                        "previous_state": ev.previous_state.value,
                        "new_state": ev.new_state.value,
                        "event_type": ev.event_type,
                        "amount_paise": ev.amount,
                        "rrn": ev.rrn,
                        "source": ev.source,
                        "provenance_complete": ev_comp,
                    }
                )

                # Add each event as a discrete verifiable candidate
                candidates.append(
                    EvidenceCandidate(
                        candidate_id=f"upi_evt_{ev.event_id}",
                        entity_type="upi_event",
                        entity_id=ev.event_id,
                        amount=ev.amount or u.amount,
                        net_financial_effect=recon_state.financial_effect_amount,
                        relationship_path=f"UPITransaction({u.upi_transaction_id}) → UPIEvent({ev.event_id}: {ev.previous_state.value} → {ev.new_state.value})",
                        temporal_status=TemporalRetrievalStatus.TEMPORALLY_VALID,
                        timestamp=ev.timestamp,
                        provenance=ev_prov,
                        is_provenance_complete=ev_comp,
                        evidence_metadata={
                            "upi_transaction_id": u.upi_transaction_id,
                            "event_type": ev.event_type,
                            "transition": f"{ev.previous_state.value} → {ev.new_state.value}",
                        },
                    )
                )

            # Add primary UPITransaction candidate with complete reconstructed state
            candidates.append(
                EvidenceCandidate(
                    candidate_id=f"upi_txn_{u.upi_transaction_id}",
                    entity_type="upi_transaction",
                    entity_id=u.upi_transaction_id,
                    amount=u.amount,
                    net_financial_effect=recon_state.financial_effect_amount,
                    relationship_path=f"Payment({u.payment_id}) → UPITransaction({u.upi_transaction_id})",
                    temporal_status=TemporalRetrievalStatus.TEMPORALLY_VALID,
                    timestamp=u.initiated_at,
                    provenance=u_prov,
                    is_provenance_complete=u_comp,
                    evidence_metadata={
                        "payment_id": u.payment_id,
                        "rrn": u.rrn,
                        "observed_status": recon_state.observed_status.value,
                        "determined_status": recon_state.determined_status.value,
                        "financial_effect_status": recon_state.financial_effect_status.value,
                        "financial_effect_amount": recon_state.financial_effect_amount,
                        "debit_observed": recon_state.debit_observed,
                        "reversal_status": recon_state.reversal_status.value,
                        "reversal_amount": recon_state.reversal_amount,
                        "reconstruction_notes": recon_state.reconstruction_notes,
                        "event_history": event_history_payload,
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
                "upi_transaction_count": len(matched_upi_txns),
                "total_upi_events_retrieved": len(candidates) - len(matched_upi_txns),
            },
        )
