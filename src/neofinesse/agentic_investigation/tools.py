from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from neofinesse.agentic_investigation.models import ToolResult
from neofinesse.ai_investigation.evidence_pack import EvidenceItem
from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.models.base import FinalDeterminedStatus, ReversalStatus, SourceEventType
from neofinesse.models.upi import UPITransaction
from neofinesse.reconciliation.upi_state import UPIStateReconstructor


class InvestigationTools:
    """Implementations of the 5 typed, bounded investigation tools."""

    @staticmethod
    def retrieve_related_evidence(
        request_id: str,
        entity_type: str,
        entity_id: str,
        relationship: str,
        dataset: IngestedDataset,
        next_ev_idx: int = 1,
    ) -> ToolResult:
        """Tool 1: Retrieve evidence directly related to a known financial entity."""
        evidence_items: List[EvidenceItem] = []
        output_data: Dict[str, Any] = {"entity_type": entity_type, "entity_id": entity_id, "relationship": relationship}

        # 1. Related to SettlementLine
        if entity_type == "settlement_line":
            line = next((l for l in dataset.settlement_lines if l.settlement_line_id == entity_id), None)
            if line:
                output_data["line"] = line.model_dump(mode="json")
                prov = line.provenance
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=f"EV-T{next_ev_idx}",
                        candidate_id=f"tool_{line.settlement_line_id}",
                        entity_id=line.settlement_line_id,
                        entity_type="settlement_line",
                        amount_paise=line.amount,
                        amount_inr=line.amount / 100.0,
                        net_financial_effect_paise=line.net_amount,
                        net_financial_effect_inr=line.net_amount / 100.0,
                        timestamp_iso=line.event_timestamp.isoformat() if line.event_timestamp else None,
                        status=line.source_event_type.value,
                        relationship_path=f"SettlementLine({line.settlement_line_id}) → {relationship}",
                        source_id=prov.source_id if prov else "SRC-LINES",
                        source_file=prov.source_file if prov else "settlement_lines.csv",
                        source_sheet=prov.source_sheet if prov else None,
                        source_row=prov.source_row if prov else 1,
                        source_hash=prov.source_hash if prov else "HASH",
                        record_hash=prov.record_hash if prov else "HASH",
                    )
                )

        # 2. Related to Payment
        elif entity_type == "payment":
            pay = next((p for p in dataset.payments if p.id == entity_id), None)
            if pay:
                output_data["payment"] = pay.model_dump(mode="json")
                prov = pay.provenance
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=f"EV-T{next_ev_idx}",
                        candidate_id=f"tool_{pay.id}",
                        entity_id=pay.id,
                        entity_type="payment",
                        amount_paise=pay.amount,
                        amount_inr=pay.amount / 100.0,
                        net_financial_effect_paise=pay.net_amount or pay.amount,
                        net_financial_effect_inr=(pay.net_amount or pay.amount) / 100.0,
                        timestamp_iso=pay.captured_at.isoformat() if pay.captured_at else None,
                        status=pay.status,
                        relationship_path=f"Payment({pay.id}) → {relationship}",
                        source_id=prov.source_id if prov else "SRC-PAYMENTS",
                        source_file=prov.source_file if prov else "payments.csv",
                        source_sheet=prov.source_sheet if prov else None,
                        source_row=prov.source_row if prov else 1,
                        source_hash=prov.source_hash if prov else "HASH",
                        record_hash=prov.record_hash if prov else "HASH",
                    )
                )

        # 3. Related to Refund
        elif entity_type == "refund":
            rfnd = next((r for r in dataset.refunds if r.id == entity_id), None)
            if rfnd:
                output_data["refund"] = rfnd.model_dump(mode="json")
                prov = rfnd.provenance
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=f"EV-T{next_ev_idx}",
                        candidate_id=f"tool_{rfnd.id}",
                        entity_id=rfnd.id,
                        entity_type="refund",
                        amount_paise=rfnd.amount,
                        amount_inr=rfnd.amount / 100.0,
                        net_financial_effect_paise=-rfnd.amount,
                        net_financial_effect_inr=-rfnd.amount / 100.0,
                        timestamp_iso=rfnd.created_at.isoformat() if rfnd.created_at else None,
                        status=rfnd.status.value if hasattr(rfnd.status, "value") else str(rfnd.status),
                        relationship_path=f"Refund({rfnd.id}) → {relationship}",
                        source_id=prov.source_id if prov else "SRC-REFUNDS",
                        source_file=prov.source_file if prov else "refunds.csv",
                        source_sheet=prov.source_sheet if prov else None,
                        source_row=prov.source_row if prov else 1,
                        source_hash=prov.source_hash if prov else "HASH",
                        record_hash=prov.record_hash if prov else "HASH",
                    )
                )

        # 4. Related to Adjustment
        elif entity_type == "adjustment":
            adj = next((a for a in dataset.adjustments if a.id == entity_id), None)
            if adj:
                output_data["adjustment"] = adj.model_dump(mode="json")
                prov = adj.provenance
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=f"EV-T{next_ev_idx}",
                        candidate_id=f"tool_{adj.id}",
                        entity_id=adj.id,
                        entity_type="adjustment",
                        amount_paise=adj.amount,
                        amount_inr=adj.amount / 100.0,
                        net_financial_effect_paise=-adj.amount,
                        net_financial_effect_inr=-adj.amount / 100.0,
                        timestamp_iso=adj.created_at.isoformat() if adj.created_at else None,
                        status=adj.type.value if hasattr(adj.type, "value") else str(adj.type),
                        relationship_path=f"Adjustment({adj.id}) → {relationship}",
                        source_id=prov.source_id if prov else "SRC-ADJUSTMENTS",
                        source_file=prov.source_file if prov else "adjustments.csv",
                        source_sheet=prov.source_sheet if prov else None,
                        source_row=prov.source_row if prov else 1,
                        source_hash=prov.source_hash if prov else "HASH",
                        record_hash=prov.record_hash if prov else "HASH",
                    )
                )

        return ToolResult(
            request_id=request_id,
            tool="retrieve_related_evidence",
            success=len(evidence_items) > 0,
            output=output_data,
            evidence_items=evidence_items,
            error=None if evidence_items else f"No entity found for {entity_type}:{entity_id}",
        )

    @staticmethod
    def verify_membership(
        request_id: str,
        event_id: str,
        settlement_id: str,
        dataset: IngestedDataset,
        next_ev_idx: int = 1,
    ) -> ToolResult:
        """Tool 2: Verify whether an event belongs to a specific settlement."""
        target_lines = [l for l in dataset.settlement_lines if l.settlement_id == settlement_id]
        batch_source_event_ids = {l.source_event_id for l in target_lines}
        batch_line_ids = {l.settlement_line_id for l in target_lines}

        is_member = (event_id in batch_source_event_ids or event_id in batch_line_ids)
        status = "MEMBER" if is_member else "NOT_MEMBER"

        evidence_items: List[EvidenceItem] = []
        matching_line = next((l for l in target_lines if l.source_event_id == event_id or l.settlement_line_id == event_id), None)

        if matching_line:
            prov = matching_line.provenance
            evidence_items.append(
                EvidenceItem(
                    evidence_id=f"EV-T{next_ev_idx}",
                    candidate_id=f"tool_member_{event_id}",
                    entity_id=event_id,
                    entity_type=matching_line.source_event_type.value.lower(),
                    amount_paise=matching_line.amount,
                    amount_inr=matching_line.amount / 100.0,
                    net_financial_effect_paise=matching_line.net_amount,
                    net_financial_effect_inr=matching_line.net_amount / 100.0,
                    timestamp_iso=matching_line.event_timestamp.isoformat() if matching_line.event_timestamp else None,
                    status=f"MEMBER_OF_{settlement_id}",
                    relationship_path=f"Settlement({settlement_id}) → SettlementLine({matching_line.settlement_line_id}) → Event({event_id})",
                    source_id=prov.source_id if prov else "SRC-LINES",
                    source_file=prov.source_file if prov else "settlement_lines.csv",
                    source_sheet=prov.source_sheet if prov else None,
                    source_row=prov.source_row if prov else 1,
                    source_hash=prov.source_hash if prov else "HASH",
                    record_hash=prov.record_hash if prov else "HASH",
                )
            )

        return ToolResult(
            request_id=request_id,
            tool="verify_membership",
            success=True,
            output={
                "event_id": event_id,
                "settlement_id": settlement_id,
                "membership_status": status,
                "line_id": matching_line.settlement_line_id if matching_line else None,
            },
            evidence_items=evidence_items,
        )

    @staticmethod
    def retrieve_upi_history(
        request_id: str,
        upi_transaction_id: str,
        dataset: IngestedDataset,
        next_ev_idx: int = 1,
    ) -> ToolResult:
        """Tool 3: Retrieve complete UPI state transition history."""
        upi_txn = next((u for u in dataset.upi_transactions if u.upi_transaction_id == upi_transaction_id), None)
        txn_events = [e for e in dataset.upi_events if e.upi_transaction_id == upi_transaction_id]

        if not upi_txn and not txn_events:
            return ToolResult(
                request_id=request_id,
                tool="retrieve_upi_history",
                success=False,
                output={"upi_transaction_id": upi_transaction_id, "status": "NOT_FOUND"},
                evidence_items=[],
                error=f"No UPI transaction events found for {upi_transaction_id}",
            )

        if not upi_txn:
            first_ev = txn_events[0]
            upi_txn = UPITransaction(
                upi_transaction_id=upi_transaction_id,
                payment_id=f"pay_{upi_transaction_id}",
                amount=first_ev.amount or 0,
                initiated_at=first_ev.timestamp,
                current_observed_status=first_ev.new_state,
                final_determined_status=FinalDeterminedStatus.INITIATED,
            )

        reconstructor = UPIStateReconstructor()
        upi_rec = reconstructor.reconstruct(upi_txn, dataset.upi_events)

        is_late_success = (upi_rec.determined_status == FinalDeterminedStatus.LATE_SUCCESS)
        is_debit_reversed = (
            upi_rec.reversal_status == ReversalStatus.SUCCESS
            or upi_rec.determined_status == FinalDeterminedStatus.REVERSED
        )
        fin_effect = upi_rec.financial_effect_amount if upi_rec.financial_effect_amount is not None else 0

        # Build chronological transition summary
        transitions = [
            {
                "event_id": e.event_id,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "event_type": e.event_type,
                "previous_state": e.previous_state.value if hasattr(e.previous_state, "value") else str(e.previous_state),
                "new_state": e.new_state.value if hasattr(e.new_state, "value") else str(e.new_state),
            }
            for e in txn_events
        ]

        # Construct new EvidenceItem with full reconstructed context
        prov = txn_events[0].provenance if txn_events else None
        ev_item = EvidenceItem(
            evidence_id=f"EV-T{next_ev_idx}",
            candidate_id=f"tool_upi_{upi_transaction_id}",
            entity_id=upi_transaction_id,
            entity_type="upi_transaction",
            amount_paise=upi_rec.amount,
            amount_inr=upi_rec.amount / 100.0,
            net_financial_effect_paise=fin_effect,
            net_financial_effect_inr=fin_effect / 100.0,
            timestamp_iso=upi_rec.latest_event_timestamp.isoformat() if upi_rec.latest_event_timestamp else None,
            status=upi_rec.determined_status.value,
            relationship_path=f"UPITransaction({upi_transaction_id}) → StateReconstruction({upi_rec.determined_status.value})",
            source_id=prov.source_id if prov else "SRC-UPI",
            source_file=prov.source_file if prov else "upi_events.csv",
            source_sheet=prov.source_sheet if prov else None,
            source_row=prov.source_row if prov else 1,
            source_hash=prov.source_hash if prov else "HASH",
            record_hash=prov.record_hash if prov else "HASH",
            evidence_metadata={
                "is_debit_reversed": is_debit_reversed,
                "is_late_success": is_late_success,
                "determined_status": upi_rec.determined_status.value,
                "debit_observed": is_debit_reversed or is_late_success or (upi_rec.determined_status.value in ("SUCCESS", "LATE_SUCCESS", "REVERSED")),
                "payment_id": upi_txn.payment_id,
                "history_length": len(transitions),
            },
        )

        return ToolResult(
            request_id=request_id,
            tool="retrieve_upi_history",
            success=True,
            output={
                "upi_transaction_id": upi_transaction_id,
                "final_status": upi_rec.determined_status.value,
                "financial_effect_paise": fin_effect,
                "is_debit_reversed": is_debit_reversed,
                "is_late_success": is_late_success,
                "transitions": transitions,
            },
            evidence_items=[ev_item],
        )

    @staticmethod
    def retrieve_temporal_neighbors(
        request_id: str,
        entity_id: str,
        reference_timestamp: str,
        window_before_minutes: int,
        window_after_minutes: int,
        dataset: IngestedDataset,
        next_ev_idx: int = 1,
    ) -> ToolResult:
        """Tool 4: Bounded temporal neighbor retrieval."""
        try:
            ref_dt = datetime.fromisoformat(reference_timestamp)
        except Exception:
            return ToolResult(
                request_id=request_id,
                tool="retrieve_temporal_neighbors",
                success=False,
                output={},
                evidence_items=[],
                error=f"Invalid ISO timestamp: {reference_timestamp}",
            )

        start_dt = ref_dt - timedelta(minutes=min(window_before_minutes, 180))
        end_dt = ref_dt + timedelta(minutes=min(window_after_minutes, 180))

        found_events: List[Dict[str, Any]] = []
        evidence_items: List[EvidenceItem] = []

        # Find candidate refunds in window
        for r in dataset.refunds:
            if r.created_at and start_dt <= r.created_at <= end_dt:
                found_events.append({"entity_type": "refund", "id": r.id, "amount": r.amount, "created_at": r.created_at.isoformat()})
                prov = r.provenance
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=f"EV-T{next_ev_idx + len(evidence_items)}",
                        candidate_id=f"tool_temporal_{r.id}",
                        entity_id=r.id,
                        entity_type="refund",
                        amount_paise=r.amount,
                        amount_inr=r.amount / 100.0,
                        net_financial_effect_paise=-r.amount,
                        net_financial_effect_inr=-r.amount / 100.0,
                        timestamp_iso=r.created_at.isoformat(),
                        status=r.status.value if hasattr(r.status, "value") else str(r.status),
                        relationship_path=f"TemporalWindow({start_dt.isoformat()}..{end_dt.isoformat()}) → Refund({r.id})",
                        source_id=prov.source_id if prov else "SRC-REFUNDS",
                        source_file=prov.source_file if prov else "refunds.csv",
                        source_sheet=prov.source_sheet if prov else None,
                        source_row=prov.source_row if prov else 1,
                        source_hash=prov.source_hash if prov else "HASH",
                        record_hash=prov.record_hash if prov else "HASH",
                    )
                )

        return ToolResult(
            request_id=request_id,
            tool="retrieve_temporal_neighbors",
            success=True,
            output={"reference": reference_timestamp, "window_matches": found_events},
            evidence_items=evidence_items,
        )

    @staticmethod
    def retrieve_source_record(
        request_id: str,
        source_id: str,
        record_id: str,
        dataset: IngestedDataset,
    ) -> ToolResult:
        """Tool 5: Direct provenance cell inspection."""
        # Find entry across all datasets
        for entity_list in [dataset.payments, dataset.refunds, dataset.disputes, dataset.adjustments, dataset.transfers, dataset.settlement_lines]:
            item = next((x for x in entity_list if getattr(x, "id", None) == record_id or getattr(x, "settlement_line_id", None) == record_id), None)
            if item and item.provenance:
                prov = item.provenance
                return ToolResult(
                    request_id=request_id,
                    tool="retrieve_source_record",
                    success=True,
                    output={
                        "source_id": prov.source_id,
                        "file": prov.source_file,
                        "sheet": prov.source_sheet,
                        "row": prov.source_row,
                        "columns": prov.source_columns,
                        "file_hash": prov.source_hash,
                        "record_hash": prov.record_hash,
                        "ingested_at": prov.ingested_at.isoformat() if prov.ingested_at else None,
                    },
                    evidence_items=[],
                )

        return ToolResult(
            request_id=request_id,
            tool="retrieve_source_record",
            success=False,
            output={"record_id": record_id, "status": "NOT_FOUND"},
            evidence_items=[],
            error=f"Provenance record not found for {record_id}",
        )
