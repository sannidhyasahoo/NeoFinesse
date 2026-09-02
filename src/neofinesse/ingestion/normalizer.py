from datetime import datetime
from typing import Any, Dict, Optional

from neofinesse.ingestion.parser import RawRecord
from neofinesse.models.base import (
    AdjustmentType,
    Currency,
    DisputePhase,
    DisputeStatus,
    FinalDeterminedStatus,
    FinancialEffectStatus,
    NormalizedObservedStatus,
    Provider,
    RefundSpeed,
    RefundStatus,
    ReversalStatus,
    SettlementReconStatus,
    SettlementStatus,
    SourceEventType,
)
from neofinesse.models.events import Adjustment, Dispute, Order, Payment, Refund, Transfer
from neofinesse.models.settlement import Settlement, SettlementLine
from neofinesse.models.upi import UPIEvent, UPITransaction
from neofinesse.models.bank import BankTransaction


def _parse_dt(val: Any) -> Optional[datetime]:
    if not val or val == "":
        return None
    if isinstance(val, datetime):
        return val
    return datetime.fromisoformat(str(val))


def _parse_int(val: Any, default: int = 0) -> int:
    if val is None or val == "":
        return default
    return int(val)


def _parse_opt_int(val: Any) -> Optional[int]:
    if val is None or val == "":
        return None
    return int(val)


def _parse_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("true", "1", "yes")


class EntityNormalizer:
    """Normalizes raw parsed records into canonical, provenance-preserving domain objects."""

    @staticmethod
    def normalize_order(raw: RawRecord) -> Order:
        d = raw.data
        return Order(
            id=str(d["id"]),
            amount=_parse_int(d["amount"]),
            currency=Currency(d.get("currency", "INR")),
            receipt=d.get("receipt") or None,
            status=str(d.get("status", "created")),
            created_at=_parse_dt(d["created_at"]),
            _provenance=raw.provenance,
        )

    @staticmethod
    def normalize_payment(raw: RawRecord) -> Payment:
        d = raw.data
        return Payment(
            id=str(d["id"]),
            amount=_parse_int(d["amount"]),
            currency=Currency(d.get("currency", "INR")),
            status=str(d["status"]),
            normalized_status=NormalizedObservedStatus(d["normalized_status"]),
            order_id=d.get("order_id") or None,
            method=str(d.get("method", "upi")),
            bank=d.get("bank") or None,
            vpa=d.get("vpa") or None,
            fee=_parse_int(d.get("fee", 0)),
            tax=_parse_int(d.get("tax", 0)),
            net_amount=_parse_int(d["net_amount"]),
            error_code=d.get("error_code") or None,
            error_description=d.get("error_description") or None,
            created_at=_parse_dt(d["created_at"]),
            captured_at=_parse_dt(d.get("captured_at")),
            settled=_parse_bool(d.get("settled", False)),
            settlement_id=d.get("settlement_id") or None,
            provider=Provider(d.get("provider", "razorpay")),
            _provenance=raw.provenance,
        )

    @staticmethod
    def normalize_upi_transaction(raw: RawRecord) -> UPITransaction:
        d = raw.data
        return UPITransaction(
            upi_transaction_id=str(d["upi_transaction_id"]),
            payment_id=str(d["payment_id"]),
            order_id=d.get("order_id") or None,
            rrn=d.get("rrn") or None,
            amount=_parse_int(d["amount"]),
            vpa=d.get("vpa") or None,
            initiated_at=_parse_dt(d["initiated_at"]),
            current_observed_status=NormalizedObservedStatus(d["current_observed_status"]),
            final_determined_status=FinalDeterminedStatus(d["final_determined_status"]),
            debit_observed=_parse_bool(d.get("debit_observed", False)),
            reversal_status=ReversalStatus(d.get("reversal_status", "NONE")),
            reversal_amount=_parse_opt_int(d.get("reversal_amount")),
            reversal_at=_parse_dt(d.get("reversal_at")),
            error_code=d.get("error_code") or None,
            error_reason=d.get("error_reason") or None,
            financial_effect_status=FinancialEffectStatus(d.get("financial_effect_status", "UNKNOWN")),
            financial_effect_amount=_parse_opt_int(d.get("financial_effect_amount")),
            provider=Provider(d.get("provider", "razorpay")),
            _provenance=raw.provenance,
        )

    @staticmethod
    def normalize_upi_event(raw: RawRecord) -> UPIEvent:
        d = raw.data
        return UPIEvent(
            event_id=str(d["event_id"]),
            upi_transaction_id=str(d["upi_transaction_id"]),
            timestamp=_parse_dt(d["timestamp"]),
            previous_state=NormalizedObservedStatus(d["previous_state"]),
            new_state=NormalizedObservedStatus(d["new_state"]),
            event_type=str(d["event_type"]),
            amount=_parse_opt_int(d.get("amount")),
            rrn=d.get("rrn") or None,
            source=str(d.get("source", "webhook")),
            _provenance=raw.provenance,
        )

    @staticmethod
    def normalize_refund(raw: RawRecord) -> Refund:
        d = raw.data
        arn = d.get("arn")
        acquirer_data = {"arn": arn} if arn else None
        return Refund(
            id=str(d["id"]),
            amount=_parse_int(d["amount"]),
            currency=Currency(d.get("currency", "INR")),
            payment_id=str(d["payment_id"]),
            status=RefundStatus(d.get("status", "processed")),
            speed_requested=RefundSpeed(d.get("speed_requested", "normal")),
            speed_processed=RefundSpeed(d.get("speed_processed", "normal")),
            acquirer_data=acquirer_data,
            created_at=_parse_dt(d["created_at"]),
            processed_at=_parse_dt(d.get("processed_at")),
            settlement_id=d.get("settlement_id") or None,
            provider=Provider(d.get("provider", "razorpay")),
            _provenance=raw.provenance,
        )

    @staticmethod
    def normalize_dispute(raw: RawRecord) -> Dispute:
        d = raw.data
        return Dispute(
            id=str(d["id"]),
            payment_id=str(d["payment_id"]),
            amount=_parse_int(d["amount"]),
            amount_deducted=_parse_int(d.get("amount_deducted", d["amount"])),
            currency=Currency(d.get("currency", "INR")),
            reason_code=d.get("reason_code") or None,
            status=DisputeStatus(d.get("status", "open")),
            phase=DisputePhase(d.get("phase", "chargeback")),
            created_at=_parse_dt(d["created_at"]),
            settlement_id=d.get("settlement_id") or None,
            reversal_settlement_id=d.get("reversal_settlement_id") or None,
            net_financial_effect=_parse_int(d.get("net_financial_effect", 0)),
            provider=Provider(d.get("provider", "razorpay")),
            _provenance=raw.provenance,
        )

    @staticmethod
    def normalize_adjustment(raw: RawRecord) -> Adjustment:
        d = raw.data
        return Adjustment(
            id=str(d["id"]),
            amount=_parse_int(d["amount"]),
            currency=Currency(d.get("currency", "INR")),
            description=d.get("description") or None,
            settlement_id=d.get("settlement_id") or None,
            adjustment_type=AdjustmentType(d.get("adjustment_type", "OTHER")),
            created_at=_parse_dt(d["created_at"]),
            provider=Provider(d.get("provider", "razorpay")),
            _provenance=raw.provenance,
        )

    @staticmethod
    def normalize_settlement_line(raw: RawRecord) -> SettlementLine:
        d = raw.data
        return SettlementLine(
            settlement_line_id=str(d["settlement_line_id"]),
            settlement_id=str(d["settlement_id"]),
            source_event_id=str(d["source_event_id"]),
            source_event_type=SourceEventType(d["source_event_type"]),
            payment_id=d.get("payment_id") or None,
            amount=_parse_int(d["amount"]),
            fee=_parse_int(d.get("fee", 0)),
            tax=_parse_int(d.get("tax", 0)),
            net_amount=_parse_int(d["net_amount"]),
            currency=Currency(d.get("currency", "INR")),
            event_timestamp=_parse_dt(d.get("event_timestamp")),
            settlement_timestamp=_parse_dt(d.get("settlement_timestamp")),
            provider=Provider(d.get("provider", "razorpay")),
            _provenance=raw.provenance,
        )

    @staticmethod
    def normalize_settlement(raw: RawRecord) -> Settlement:
        d = raw.data
        return Settlement(
            id=str(d["id"]),
            amount=_parse_int(d["amount"]),
            status=SettlementStatus(d.get("status", "processed")),
            fees=_parse_int(d.get("fees", 0)),
            tax=_parse_int(d.get("tax", 0)),
            utr=d.get("utr") or None,
            gross_amount=_parse_int(d.get("gross_amount", 0)),
            refund_total=_parse_int(d.get("refund_total", 0)),
            adjustment_total=_parse_int(d.get("adjustment_total", 0)),
            dispute_total=_parse_int(d.get("dispute_total", 0)),
            transfer_total=_parse_int(d.get("transfer_total", 0)),
            expected_amount=_parse_int(d["expected_amount"]),
            variance=_parse_int(d.get("variance", 0)),
            recon_status=SettlementReconStatus(d.get("recon_status", "MATCHED")),
            created_at=_parse_dt(d["created_at"]),
            settled_at=_parse_dt(d.get("settled_at")),
            provider=Provider(d.get("provider", "razorpay")),
            _provenance=raw.provenance,
        )

    @staticmethod
    def normalize_bank_transaction(raw: RawRecord) -> BankTransaction:
        d = raw.data
        return BankTransaction(
            bank_txn_id=str(d["bank_txn_id"]),
            utr=d.get("utr") or None,
            credit_amount=_parse_opt_int(d.get("credit_amount")),
            debit_amount=_parse_opt_int(d.get("debit_amount")),
            balance=_parse_opt_int(d.get("balance")),
            value_date=_parse_dt(d["value_date"]),
            transaction_date=_parse_dt(d["transaction_date"]),
            raw_description=str(d.get("raw_description", "")),
            parsed_utr=d.get("parsed_utr") or None,
            account_number=str(d.get("account_number", "ACC9988776655")),
            _provenance=raw.provenance,
        )
