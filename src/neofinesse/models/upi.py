from datetime import datetime
from typing import Optional
from pydantic import Field

from neofinesse.models.base import (
    BaseDomainModel,
    FinalDeterminedStatus,
    FinancialEffectStatus,
    NormalizedObservedStatus,
    Provider,
    ReversalStatus,
)


class UPITransaction(BaseDomainModel):
    upi_transaction_id: str = Field(description="UPI transaction identifier (e.g. upi_XXXX)")
    payment_id: str = Field(description="FK to Payment")
    order_id: Optional[str] = Field(default=None, description="FK to Order")
    rrn: Optional[str] = Field(default=None, description="Retrieval Reference Number (12 digits)")
    amount: int = Field(ge=0, description="Transaction amount in paise")
    vpa: Optional[str] = Field(default=None, description="UPI Virtual Payment Address")
    initiated_at: datetime = Field(description="Initiation timestamp")
    current_observed_status: NormalizedObservedStatus = Field(
        description="[Observed Fact] Latest status reported by provider"
    )
    final_determined_status: FinalDeterminedStatus = Field(
        description="[Inferred Conclusion] State computed from complete event history"
    )
    debit_observed: bool = Field(default=False, description="[Observed Fact] Whether customer debit is evidenced")
    reversal_status: ReversalStatus = Field(default=ReversalStatus.NONE, description="[Observed Fact] Reversal state")
    reversal_amount: Optional[int] = Field(default=None, description="Reversed amount in paise")
    reversal_at: Optional[datetime] = Field(default=None, description="Reversal timestamp")
    error_code: Optional[str] = Field(default=None)
    error_reason: Optional[str] = Field(default=None)
    financial_effect_status: FinancialEffectStatus = Field(
        default=FinancialEffectStatus.UNKNOWN,
        description="[Type-Safe Semantics] DETERMINED or UNKNOWN"
    )
    financial_effect_amount: Optional[int] = Field(
        default=None,
        description="[Type-Safe Semantics] Signed amount in paise (null if UNKNOWN)"
    )
    provider: Provider = Field(default=Provider.RAZORPAY)


class UPIEvent(BaseDomainModel):
    event_id: str = Field(description="UPI event identifier (e.g. upievt_XXXX)")
    upi_transaction_id: str = Field(description="FK to UPI Transaction")
    timestamp: datetime = Field(description="Event timestamp")
    previous_state: NormalizedObservedStatus = Field(description="State before transition")
    new_state: NormalizedObservedStatus = Field(description="State after transition")
    event_type: str = Field(description="Event type (e.g. WEBHOOK_INITIATED, LATE_AUTH_CONFIRMATION, REVERSAL_CREDIT)")
    amount: Optional[int] = Field(default=None, description="Amount in paise if applicable")
    rrn: Optional[str] = Field(default=None, description="Reference number if available")
    source: str = Field(default="webhook", description="Evidence source (e.g. webhook, gateway_api, bank_feed)")
