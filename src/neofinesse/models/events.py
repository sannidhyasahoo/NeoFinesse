from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import ConfigDict, Field

from neofinesse.models.base import (
    AdjustmentType,
    BaseDomainModel,
    Currency,
    DisputePhase,
    DisputeStatus,
    NormalizedObservedStatus,
    Provider,
    RefundSpeed,
    RefundStatus,
)


class Order(BaseDomainModel):
    id: str = Field(description="Order identifier (e.g. order_XXXX)")
    entity: str = Field(default="order")
    amount: int = Field(ge=0, description="Order amount in paise")
    currency: Currency = Field(default=Currency.INR)
    receipt: Optional[str] = Field(default=None)
    status: str = Field(default="created", description="Order status")
    created_at: datetime = Field(description="Creation timestamp")


class Payment(BaseDomainModel):
    id: str = Field(description="Payment identifier (e.g. pay_XXXX)")
    entity: str = Field(default="payment")
    amount: int = Field(ge=0, description="Gross payment amount in paise")
    currency: Currency = Field(default=Currency.INR)
    status: str = Field(description="Raw provider status (e.g. created, authorized, captured, refunded, failed)")
    normalized_status: NormalizedObservedStatus = Field(description="Standardized provider-observed status")
    order_id: Optional[str] = Field(default=None, description="FK to Order")
    method: str = Field(default="upi", description="Payment method: upi, card, netbanking, wallet, emandate, bank_transfer")
    description: Optional[str] = Field(default=None)
    bank: Optional[str] = Field(default=None, description="Issuing bank code (e.g. HDFC, SBIN)")
    wallet: Optional[str] = Field(default=None)
    vpa: Optional[str] = Field(default=None, description="Payer UPI VPA")
    email: Optional[str] = Field(default=None)
    contact: Optional[str] = Field(default=None)
    fee: int = Field(default=0, ge=0, description="Gateway fee in paise")
    tax: int = Field(default=0, ge=0, description="Tax on fee in paise")
    net_amount: int = Field(description="Computed: amount - fee - tax (paise)")
    error_code: Optional[str] = Field(default=None)
    error_description: Optional[str] = Field(default=None)
    error_source: Optional[str] = Field(default=None)
    error_step: Optional[str] = Field(default=None)
    error_reason: Optional[str] = Field(default=None)
    acquirer_data: Optional[Dict[str, Any]] = Field(default=None, description="e.g. {'rrn': '...', 'auth_code': '...'}")
    created_at: datetime = Field(description="Payment creation timestamp")
    captured_at: Optional[datetime] = Field(default=None, description="Capture timestamp if captured")
    settled: bool = Field(default=False, description="Whether payment is settled")
    settlement_id: Optional[str] = Field(default=None, description="[Denormalized convenience field] FK to Settlement")
    provider: Provider = Field(default=Provider.RAZORPAY)


class Refund(BaseDomainModel):
    id: str = Field(description="Refund identifier (e.g. rfnd_XXXX)")
    entity: str = Field(default="refund")
    amount: int = Field(gt=0, description="Refund amount in paise")
    currency: Currency = Field(default=Currency.INR)
    payment_id: str = Field(description="FK to parent Payment")
    status: RefundStatus = Field(default=RefundStatus.PROCESSED)
    speed_requested: RefundSpeed = Field(default=RefundSpeed.NORMAL)
    speed_processed: RefundSpeed = Field(default=RefundSpeed.NORMAL)
    receipt: Optional[str] = Field(default=None)
    acquirer_data: Optional[Dict[str, Any]] = Field(default=None, description="e.g. {'arn': '...'}")
    created_at: datetime = Field(description="Refund creation timestamp")
    processed_at: Optional[datetime] = Field(default=None, description="Refund processing timestamp")
    settlement_id: Optional[str] = Field(default=None, description="[Denormalized convenience field] Target settlement batch")
    provider: Provider = Field(default=Provider.RAZORPAY)


class Dispute(BaseDomainModel):
    id: str = Field(description="Dispute identifier (e.g. disp_XXXX)")
    entity: str = Field(default="dispute")
    payment_id: str = Field(description="FK to parent Payment")
    amount: int = Field(gt=0, description="Disputed amount in paise")
    currency: Currency = Field(default=Currency.INR)
    amount_deducted: int = Field(ge=0, description="Amount deducted by gateway in paise")
    reason_code: Optional[str] = Field(default=None)
    respond_by: Optional[datetime] = Field(default=None)
    status: DisputeStatus = Field(default=DisputeStatus.OPEN)
    phase: DisputePhase = Field(default=DisputePhase.CHARGEBACK)
    created_at: datetime = Field(description="Dispute initiation timestamp")
    settlement_id: Optional[str] = Field(default=None, description="[Denormalized convenience field] Deduction settlement batch")
    reversal_settlement_id: Optional[str] = Field(default=None, description="[Denormalized convenience field] Credit settlement batch if won")
    net_financial_effect: int = Field(default=0, description="Computed net effect: -amount_deducted if lost, 0 if won/reversed")
    provider: Provider = Field(default=Provider.RAZORPAY)


class Adjustment(BaseDomainModel):
    id: str = Field(description="Adjustment identifier (e.g. adj_XXXX)")
    entity: str = Field(default="adjustment")
    amount: int = Field(description="Signed adjustment amount in paise (positive=credit, negative=debit)")
    currency: Currency = Field(default=Currency.INR)
    description: Optional[str] = Field(default=None)
    settlement_id: Optional[str] = Field(default=None, description="[Denormalized convenience field] Linked settlement")
    adjustment_type: AdjustmentType = Field(default=AdjustmentType.OTHER)
    created_at: datetime = Field(description="Adjustment timestamp")
    provider: Provider = Field(default=Provider.RAZORPAY)


class Transfer(BaseDomainModel):
    id: str = Field(description="Transfer identifier (e.g. trf_XXXX)")
    entity: str = Field(default="transfer")
    amount: int = Field(gt=0, description="Transfer amount in paise")
    currency: Currency = Field(default=Currency.INR)
    recipient: str = Field(description="Recipient account identifier")
    settlement_id: Optional[str] = Field(default=None, description="[Denormalized convenience field] Linked settlement")
    created_at: datetime = Field(description="Transfer timestamp")
    provider: Provider = Field(default=Provider.RAZORPAY)
