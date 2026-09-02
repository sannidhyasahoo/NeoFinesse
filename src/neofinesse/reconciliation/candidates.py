from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.models.base import ProvenanceReference, SourceEventType
from neofinesse.models.events import Adjustment, Dispute, Payment, Refund, Transfer
from neofinesse.models.settlement import Settlement, SettlementLine
from neofinesse.models.upi import UPITransaction


class CandidateEvent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    candidate_id: str
    entity_type: str  # refund, dispute, adjustment, payment, transfer, upi_transaction
    entity_id: str
    settlement_line_id: Optional[str] = None
    settlement_id: Optional[str] = None
    amount: int  # Gross amount in paise
    net_financial_effect: int  # Signed financial contribution in paise (- for deduction, + for credit)
    relationship_path: str
    timestamp: datetime
    is_settlement_constituent: bool = False
    payment_id: Optional[str] = None
    provenance: Optional[ProvenanceReference] = None


class CandidateRetriever:
    """Retrieves candidates through explicit entity relationships and batch association."""

    def retrieve_candidates_for_settlement(
        self,
        settlement: Settlement,
        settlement_lines: List[SettlementLine],
        payments: List[Payment],
        refunds: List[Refund],
        disputes: List[Dispute],
        adjustments: List[Adjustment],
        transfers: List[Transfer],
        upi_txns: List[UPITransaction],
    ) -> List[CandidateEvent]:
        """Constructs the candidate set for a target settlement through explicit relational traversals."""
        candidates: List[CandidateEvent] = []

        # 1. Target settlement's constituent settlement lines
        target_lines = [l for l in settlement_lines if l.settlement_id == settlement.id]
        line_source_ids = {l.source_event_id for l in target_lines}
        line_by_source = {l.source_event_id: l for l in target_lines}

        # Index helper maps
        refund_by_id = {r.id: r for r in refunds}
        dispute_by_id = {d.id: d for d in disputes}
        adjustment_by_id = {a.id: a for a in adjustments}
        transfer_by_id = {t.id: t for t in transfers}
        payment_by_id = {p.id: p for p in payments}
        upi_by_payment = {u.payment_id: u for u in upi_txns}

        # 1. Deductions directly in SettlementLines (Refunds, Adjustments, Disputes)
        for line in target_lines:
            if line.source_event_type == SourceEventType.REFUND:
                rfnd = refund_by_id.get(line.source_event_id)
                candidates.append(
                    CandidateEvent(
                        candidate_id=f"cand_{line.settlement_line_id}",
                        entity_type="refund",
                        entity_id=line.source_event_id,
                        settlement_line_id=line.settlement_line_id,
                        settlement_id=settlement.id,
                        amount=line.amount,
                        net_financial_effect=line.net_amount,  # negative
                        relationship_path=f"Settlement({settlement.id}) → SettlementLine({line.settlement_line_id}) → Refund({line.source_event_id})",
                        timestamp=line.event_timestamp or settlement.created_at,
                        is_settlement_constituent=True,
                        payment_id=line.payment_id,
                        provenance=rfnd.provenance if rfnd else line.provenance,
                    )
                )
            elif line.source_event_type == SourceEventType.ADJUSTMENT:
                adj = adjustment_by_id.get(line.source_event_id)
                candidates.append(
                    CandidateEvent(
                        candidate_id=f"cand_{line.settlement_line_id}",
                        entity_type="adjustment",
                        entity_id=line.source_event_id,
                        settlement_line_id=line.settlement_line_id,
                        settlement_id=settlement.id,
                        amount=line.amount,
                        net_financial_effect=line.net_amount,
                        relationship_path=f"Settlement({settlement.id}) → SettlementLine({line.settlement_line_id}) → Adjustment({line.source_event_id})",
                        timestamp=line.event_timestamp or settlement.created_at,
                        is_settlement_constituent=True,
                        payment_id=None,
                        provenance=adj.provenance if adj else line.provenance,
                    )
                )
            elif line.source_event_type in (SourceEventType.DISPUTE, SourceEventType.DISPUTE_REVERSAL):
                disp = dispute_by_id.get(line.source_event_id)
                candidates.append(
                    CandidateEvent(
                        candidate_id=f"cand_{line.settlement_line_id}",
                        entity_type="dispute",
                        entity_id=line.source_event_id,
                        settlement_line_id=line.settlement_line_id,
                        settlement_id=settlement.id,
                        amount=line.amount,
                        net_financial_effect=line.net_amount,
                        relationship_path=f"Settlement({settlement.id}) → SettlementLine({line.settlement_line_id}) → Dispute({line.source_event_id})",
                        timestamp=line.event_timestamp or settlement.created_at,
                        is_settlement_constituent=True,
                        payment_id=line.payment_id,
                        provenance=disp.provenance if disp else line.provenance,
                    )
                )
            elif line.source_event_type == SourceEventType.PAYMENT:
                # Check if this payment had an associated UPI late success
                upi = upi_by_payment.get(line.source_event_id)
                if upi:
                    candidates.append(
                        CandidateEvent(
                            candidate_id=f"cand_upi_{upi.upi_transaction_id}",
                            entity_type="upi_transaction",
                            entity_id=upi.upi_transaction_id,
                            settlement_line_id=line.settlement_line_id,
                            settlement_id=settlement.id,
                            amount=upi.amount,
                            net_financial_effect=line.net_amount,
                            relationship_path=f"Settlement({settlement.id}) → SettlementLine({line.settlement_line_id}) → Payment({line.source_event_id}) → UPITransaction({upi.upi_transaction_id})",
                            timestamp=line.event_timestamp or settlement.created_at,
                            is_settlement_constituent=True,
                            payment_id=line.source_event_id,
                            provenance=upi.provenance or line.provenance,
                        )
                    )

        # 2. Retrieve external / unassigned refunds for payments in this batch
        batch_payment_ids = {l.source_event_id for l in target_lines if l.source_event_type == SourceEventType.PAYMENT}
        for r in refunds:
            if r.id not in line_source_ids and (r.payment_id in batch_payment_ids or r.settlement_id == settlement.id):
                candidates.append(
                    CandidateEvent(
                        candidate_id=f"cand_ext_rfnd_{r.id}",
                        entity_type="refund",
                        entity_id=r.id,
                        settlement_line_id=None,
                        settlement_id=r.settlement_id,
                        amount=r.amount,
                        net_financial_effect=-r.amount,
                        relationship_path=f"Payment({r.payment_id}) → Refund({r.id})",
                        timestamp=r.processed_at or r.created_at,
                        is_settlement_constituent=False,
                        payment_id=r.payment_id,
                        provenance=r.provenance,
                    )
                )

        # 3. Retrieve external disputes on payments in this batch
        for d in disputes:
            if d.id not in line_source_ids and (d.payment_id in batch_payment_ids or d.settlement_id == settlement.id):
                candidates.append(
                    CandidateEvent(
                        candidate_id=f"cand_ext_disp_{d.id}",
                        entity_type="dispute",
                        entity_id=d.id,
                        settlement_line_id=None,
                        settlement_id=d.settlement_id,
                        amount=d.amount_deducted,
                        net_financial_effect=-d.amount_deducted,
                        relationship_path=f"Payment({d.payment_id}) → Dispute({d.id})",
                        timestamp=d.created_at,
                        is_settlement_constituent=False,
                        payment_id=d.payment_id,
                        provenance=d.provenance,
                    )
                )

        # 4. Include external same-batch adjustments not yet in lines
        for a in adjustments:
            if a.id not in line_source_ids and a.settlement_id == settlement.id:
                candidates.append(
                    CandidateEvent(
                        candidate_id=f"cand_ext_adj_{a.id}",
                        entity_type="adjustment",
                        entity_id=a.id,
                        settlement_line_id=None,
                        settlement_id=a.settlement_id,
                        amount=abs(a.amount),
                        net_financial_effect=a.amount,
                        relationship_path=f"Settlement({settlement.id}) → Adjustment({a.id})",
                        timestamp=a.created_at,
                        is_settlement_constituent=False,
                        payment_id=None,
                        provenance=a.provenance,
                    )
                )

        # 5. Include global candidate events within temporal proximity for adversarial decoy testing
        settle_time = settlement.settled_at or settlement.created_at
        for r in refunds:
            if r.id not in line_source_ids and r.payment_id not in batch_payment_ids and r.settlement_id != settlement.id:
                candidates.append(
                    CandidateEvent(
                        candidate_id=f"cand_decoy_rfnd_{r.id}",
                        entity_type="refund",
                        entity_id=r.id,
                        settlement_line_id=None,
                        settlement_id=r.settlement_id,
                        amount=r.amount,
                        net_financial_effect=-r.amount,
                        relationship_path=f"Unrelated Payment({r.payment_id}) → Refund({r.id}) in Settlement({r.settlement_id})",
                        timestamp=r.processed_at or r.created_at,
                        is_settlement_constituent=False,
                        payment_id=r.payment_id,
                        provenance=r.provenance,
                    )
                )
        for d in disputes:
            if d.id not in line_source_ids and d.payment_id not in batch_payment_ids and d.settlement_id != settlement.id:
                candidates.append(
                    CandidateEvent(
                        candidate_id=f"cand_decoy_disp_{d.id}",
                        entity_type="dispute",
                        entity_id=d.id,
                        settlement_line_id=None,
                        settlement_id=d.settlement_id,
                        amount=d.amount_deducted,
                        net_financial_effect=-d.amount_deducted,
                        relationship_path=f"Unrelated Payment({d.payment_id}) → Dispute({d.id}) in Settlement({d.settlement_id})",
                        timestamp=d.created_at,
                        is_settlement_constituent=False,
                        payment_id=d.payment_id,
                        provenance=d.provenance,
                    )
                )

        return candidates
