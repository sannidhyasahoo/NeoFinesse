from datetime import datetime
from typing import Optional
from pydantic import Field

from neofinesse.models.base import (
    BaseDomainModel,
    Currency,
    Provider,
    SettlementReconStatus,
    SettlementStatus,
    SourceEventType,
)


class SettlementLine(BaseDomainModel):
    settlement_line_id: str = Field(description="Unique settlement line identifier (e.g. line_XXXX)")
    settlement_id: str = Field(description="FK to Settlement")
    source_event_id: str = Field(description="Underlying financial event ID (e.g. pay_XXXX, rfnd_XXXX)")
    source_event_type: SourceEventType = Field(description="Event type (PAYMENT, REFUND, DISPUTE, etc.)")
    payment_id: Optional[str] = Field(default=None, description="FK to parent Payment if applicable")
    amount: int = Field(ge=0, description="Gross amount of the line item in paise")
    fee: int = Field(default=0, ge=0, description="Attributed gateway fee in paise")
    tax: int = Field(default=0, ge=0, description="Attributed tax on fee in paise")
    net_amount: int = Field(description="Signed net contribution to settlement in paise (+ for credit, - for debit)")
    currency: Currency = Field(default=Currency.INR)
    event_timestamp: Optional[datetime] = Field(default=None, description="Source event timestamp")
    settlement_timestamp: Optional[datetime] = Field(default=None, description="Settlement processing timestamp")
    provider: Provider = Field(default=Provider.RAZORPAY)


class Settlement(BaseDomainModel):
    id: str = Field(description="Settlement batch identifier (e.g. setl_XXXX)")
    entity: str = Field(default="settlement")
    amount: int = Field(description="Actual net settled amount reported by provider in paise")
    status: SettlementStatus = Field(default=SettlementStatus.PROCESSED)
    fees: int = Field(default=0, ge=0, description="Total gateway fees deducted in paise")
    tax: int = Field(default=0, ge=0, description="Total tax deducted in paise")
    utr: Optional[str] = Field(default=None, description="Bank Unique Transaction Reference (e.g. AXISCN1153863727)")
    gross_amount: int = Field(default=0, ge=0, description="Total gross payment volume in batch (paise)")
    refund_total: int = Field(default=0, ge=0, description="Total refund deductions in batch (paise)")
    adjustment_total: int = Field(default=0, description="Total adjustment contribution (signed paise)")
    dispute_total: int = Field(default=0, ge=0, description="Total dispute deductions in batch (paise)")
    transfer_total: int = Field(default=0, ge=0, description="Total transfers in batch (paise)")
    expected_amount: int = Field(description="NeoFinesse mathematically verified sum of SettlementLine.net_amount in paise")
    variance: int = Field(default=0, description="expected_amount - amount (paise)")
    bank_credit_amount: Optional[int] = Field(default=None, description="Matched bank credit amount in paise")
    bank_credit_date: Optional[datetime] = Field(default=None, description="Bank statement value date")
    bank_reference: Optional[str] = Field(default=None, description="Bank side reference narration")
    recon_status: SettlementReconStatus = Field(default=SettlementReconStatus.MATCHED)
    created_at: datetime = Field(description="Settlement batch creation timestamp")
    settled_at: Optional[datetime] = Field(default=None, description="Settlement transfer timestamp")
    provider: Provider = Field(default=Provider.RAZORPAY)
