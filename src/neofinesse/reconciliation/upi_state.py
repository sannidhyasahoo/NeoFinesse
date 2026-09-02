from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.models.base import (
    FinalDeterminedStatus,
    FinancialEffectStatus,
    NormalizedObservedStatus,
    ReversalStatus,
)
from neofinesse.models.upi import UPIEvent, UPITransaction


class UPIReconstructedState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    upi_transaction_id: str
    payment_id: str
    amount: int
    event_count: int
    latest_event_timestamp: Optional[datetime] = None
    observed_status: NormalizedObservedStatus
    determined_status: FinalDeterminedStatus
    financial_effect_status: FinancialEffectStatus
    financial_effect_amount: Optional[int] = None
    debit_observed: bool = False
    reversal_status: ReversalStatus = ReversalStatus.NONE
    reversal_amount: Optional[int] = None
    reconstruction_notes: str


class UPIStateReconstructor:
    """Reconstructs the true financial state of UPI transactions from their chronological event history."""

    def reconstruct(self, upi_txn: UPITransaction, events: List[UPIEvent]) -> UPIReconstructedState:
        """Reconstructs state and derives type-safe financial effects from event sequence."""
        # Filter and sort events for this transaction
        txn_events = [e for e in events if e.upi_transaction_id == upi_txn.upi_transaction_id]
        txn_events.sort(key=lambda x: x.timestamp)

        if not txn_events:
            # Fallback to current transaction fields if no event log exists
            return UPIReconstructedState(
                upi_transaction_id=upi_txn.upi_transaction_id,
                payment_id=upi_txn.payment_id,
                amount=upi_txn.amount,
                event_count=0,
                observed_status=upi_txn.current_observed_status,
                determined_status=upi_txn.final_determined_status,
                financial_effect_status=upi_txn.financial_effect_status,
                financial_effect_amount=upi_txn.financial_effect_amount,
                debit_observed=upi_txn.debit_observed,
                reversal_status=upi_txn.reversal_status,
                reversal_amount=upi_txn.reversal_amount,
                reconstruction_notes="No event log found; retained observed provider status.",
            )

        latest_event = txn_events[-1]
        observed_status = latest_event.new_state
        debit_observed = upi_txn.debit_observed
        reversal_status = upi_txn.reversal_status
        reversal_amount = upi_txn.reversal_amount

        # Check event sequence for state signatures
        has_initial_failure = any(e.new_state == NormalizedObservedStatus.FAILED for e in txn_events)
        has_late_success = has_initial_failure and latest_event.new_state in (
            NormalizedObservedStatus.CAPTURED,
            NormalizedObservedStatus.PENDING,
        )
        has_reversal_event = any("REVERSAL" in e.event_type.upper() for e in txn_events)
        has_debit_event = any("DEBIT" in e.event_type.upper() for e in txn_events)

        if has_debit_event:
            debit_observed = True
        if has_reversal_event:
            reversal_status = ReversalStatus.SUCCESS
            reversal_amount = upi_txn.amount

        # Derive final determined status and financial effect
        if has_late_success or (has_initial_failure and observed_status == NormalizedObservedStatus.CAPTURED):
            determined_status = FinalDeterminedStatus.LATE_SUCCESS
            effect_status = FinancialEffectStatus.DETERMINED
            effect_amount = upi_txn.amount
            notes = f"Late authorization confirmed at {latest_event.timestamp.isoformat()} after initial bank failure. Financial effect = +{upi_txn.amount} paise."

        elif observed_status == NormalizedObservedStatus.CAPTURED:
            determined_status = FinalDeterminedStatus.SUCCESS
            effect_status = FinancialEffectStatus.DETERMINED
            effect_amount = upi_txn.amount
            notes = f"Confirmed captured payment. Financial effect = +{upi_txn.amount} paise."

        elif observed_status == NormalizedObservedStatus.FAILED:
            determined_status = FinalDeterminedStatus.FAILED
            if not debit_observed:
                effect_status = FinancialEffectStatus.DETERMINED
                effect_amount = 0
                notes = "Clean payment failure with no customer debit. Financial effect = 0 paise."
            elif reversal_status == ReversalStatus.SUCCESS:
                effect_status = FinancialEffectStatus.DETERMINED
                effect_amount = 0
                notes = f"Failed transaction debited customer but auto-reversal succeeded for ₹{reversal_amount/100:.2f}. Net financial effect = 0 paise."
            else:
                effect_status = FinancialEffectStatus.UNKNOWN
                effect_amount = None
                notes = "Customer debit observed on failed transaction but no reversal evidence found in dataset. Financial effect UNKNOWN (escalated)."

        elif observed_status in (NormalizedObservedStatus.PENDING, NormalizedObservedStatus.INITIATED):
            determined_status = FinalDeterminedStatus.PENDING
            effect_status = FinancialEffectStatus.UNKNOWN
            effect_amount = None
            notes = "In-flight / pending transaction awaiting terminal confirmation. Financial effect UNKNOWN."

        elif observed_status == NormalizedObservedStatus.REFUNDED:
            determined_status = FinalDeterminedStatus.REVERSED
            effect_status = FinancialEffectStatus.DETERMINED
            effect_amount = 0
            notes = "Fully refunded transaction. Net financial effect = 0 paise."

        else:
            determined_status = FinalDeterminedStatus.INITIATED
            effect_status = FinancialEffectStatus.UNKNOWN
            effect_amount = None
            notes = f"Unresolved state {observed_status}."

        return UPIReconstructedState(
            upi_transaction_id=upi_txn.upi_transaction_id,
            payment_id=upi_txn.payment_id,
            amount=upi_txn.amount,
            event_count=len(txn_events),
            latest_event_timestamp=latest_event.timestamp,
            observed_status=observed_status,
            determined_status=determined_status,
            financial_effect_status=effect_status,
            financial_effect_amount=effect_amount,
            debit_observed=debit_observed,
            reversal_status=reversal_status,
            reversal_amount=reversal_amount,
            reconstruction_notes=notes,
        )
