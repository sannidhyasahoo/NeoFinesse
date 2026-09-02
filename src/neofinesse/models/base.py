from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class Provider(str, Enum):
    RAZORPAY = "razorpay"
    CASHFREE = "cashfree"
    STRIPE = "stripe"
    AIRWALLEX = "airwallex"
    BANK = "bank"


class Currency(str, Enum):
    INR = "INR"


class SourceType(str, Enum):
    CSV = "CSV"
    XLSX = "XLSX"
    XLS = "XLS"
    API_RESPONSE = "API_RESPONSE"
    WEBHOOK = "WEBHOOK"


class FinancialEffectStatus(str, Enum):
    DETERMINED = "DETERMINED"
    UNKNOWN = "UNKNOWN"


class NormalizedObservedStatus(str, Enum):
    INITIATED = "INITIATED"
    PENDING = "PENDING"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class FinalDeterminedStatus(str, Enum):
    INITIATED = "INITIATED"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REVERSED = "REVERSED"
    LATE_SUCCESS = "LATE_SUCCESS"


class SettlementStatus(str, Enum):
    CREATED = "created"
    PROCESSED = "processed"
    FAILED = "failed"


class SettlementReconStatus(str, Enum):
    MATCHED = "MATCHED"
    VARIANCE_DETECTED = "VARIANCE_DETECTED"
    PENDING_BANK_CREDIT = "PENDING_BANK_CREDIT"
    FAILED = "FAILED"


class SourceEventType(str, Enum):
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"
    DISPUTE = "DISPUTE"
    DISPUTE_REVERSAL = "DISPUTE_REVERSAL"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER = "TRANSFER"
    FEE_LINE = "FEE_LINE"
    TAX_LINE = "TAX_LINE"


class AdjustmentType(str, Enum):
    FEE = "FEE"
    TAX = "TAX"
    RISK_HOLD = "RISK_HOLD"
    RISK_RELEASE = "RISK_RELEASE"
    MANUAL_CREDIT = "MANUAL_CREDIT"
    MANUAL_DEBIT = "MANUAL_DEBIT"
    RESERVE_HOLD = "RESERVE_HOLD"
    RESERVE_RELEASE = "RESERVE_RELEASE"
    OTHER = "OTHER"


class DisputeStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    WON = "won"
    LOST = "lost"
    CLOSED = "closed"


class DisputePhase(str, Enum):
    CHARGEBACK = "chargeback"
    PRE_ARBITRATION = "pre_arbitration"
    ARBITRATION = "arbitration"


class RefundStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class RefundSpeed(str, Enum):
    NORMAL = "normal"
    OPTIMUM = "optimum"
    INSTANT = "instant"


class ReversalStatus(str, Enum):
    NONE = "NONE"
    INITIATED = "INITIATED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class EvidenceLevel(str, Enum):
    L0 = "L0"  # Candidate (Amount only)
    L1 = "L1"  # Entity-linked
    L2 = "L2"  # Settlement-associated
    L3 = "L3"  # Temporally consistent
    L4 = "L4"  # Financially complete (Subset-sum exact)
    L5 = "L5"  # Multi-source verified (Bank UTR confirmed)


class ProvenanceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(description="Unique ingestion identifier (e.g. SRC-2026-0001)")
    source_type: SourceType = Field(description="Transport/file format")
    source_file: str = Field(description="Original source file name")
    source_sheet: Optional[str] = Field(default=None, description="Sheet name for Excel, null for CSV")
    source_row: int = Field(ge=1, description="1-indexed row number (header = 1)")
    source_columns: Optional[Dict[str, str]] = Field(default=None, description="Mapping of semantic field to cell (e.g. {'amount': 'D193'})")
    source_hash: str = Field(description="SHA-256 hash of entire source file")
    record_hash: str = Field(description="SHA-256 hash of exact source row / payload")
    provider: Provider = Field(description="Originating provider")
    ingested_at: datetime = Field(description="Ingestion timestamp")
    ingested_by: str = Field(description="Ingestion batch / worker ID")


class BaseDomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provenance: Optional[ProvenanceReference] = Field(default=None, alias="_provenance", description="Full audit provenance")
