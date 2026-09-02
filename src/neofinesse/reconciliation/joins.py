from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.models.base import ProvenanceReference
from neofinesse.models.settlement import Settlement
from neofinesse.models.bank import BankTransaction


class BankJoinStatus:
    EXACT_UTR_MATCH = "EXACT_UTR_MATCH"
    DELAYED_BANK_CREDIT = "DELAYED_BANK_CREDIT"
    MISSING_BANK_TRANSACTION = "MISSING_BANK_TRANSACTION"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    AMBIGUOUS_MATCH = "AMBIGUOUS_MATCH"


class BankJoinResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    settlement_id: str
    utr: Optional[str]
    settlement_amount: int
    bank_txn: Optional[BankTransaction] = None
    bank_amount: Optional[int] = None
    join_status: str
    variance: int = 0  # actual_bank_credit - settlement_amount
    clearing_delay_hours: Optional[float] = None
    notes: Optional[str] = None


class BankJoinEngine:
    """Deterministic bank join engine matching gateway settlements to bank transactions via UTR."""

    def __init__(self, max_clearing_window_hours: float = 48.0):
        self.max_clearing_window_hours = max_clearing_window_hours

    def match_settlements_to_bank(
        self, settlements: List[Settlement], bank_txns: List[BankTransaction]
    ) -> Dict[str, BankJoinResult]:
        """Matches each settlement to bank transactions using definitive UTR exact string matching."""
        # Index bank transactions by UTR
        bank_by_utr: Dict[str, List[BankTransaction]] = {}
        for b in bank_txns:
            effective_utr = b.parsed_utr or b.utr
            if effective_utr:
                bank_by_utr.setdefault(effective_utr.strip().upper(), []).append(b)

        results: Dict[str, BankJoinResult] = {}

        for s in settlements:
            s_utr = s.utr.strip().upper() if s.utr else None

            if not s_utr:
                results[s.id] = BankJoinResult(
                    settlement_id=s.id,
                    utr=None,
                    settlement_amount=s.amount,
                    bank_txn=None,
                    bank_amount=None,
                    join_status=BankJoinStatus.MISSING_BANK_TRANSACTION,
                    variance=-s.amount,
                    notes="Settlement has no UTR assigned by gateway.",
                )
                continue

            matching_txns = bank_by_utr.get(s_utr, [])

            if not matching_txns:
                # Check if this could be an in-flight / pending clearing
                results[s.id] = BankJoinResult(
                    settlement_id=s.id,
                    utr=s_utr,
                    settlement_amount=s.amount,
                    bank_txn=None,
                    bank_amount=None,
                    join_status=BankJoinStatus.MISSING_BANK_TRANSACTION,
                    variance=-s.amount,
                    notes=f"No bank credit found matching UTR {s_utr}.",
                )
            elif len(matching_txns) > 1:
                results[s.id] = BankJoinResult(
                    settlement_id=s.id,
                    utr=s_utr,
                    settlement_amount=s.amount,
                    bank_txn=matching_txns[0],
                    bank_amount=matching_txns[0].credit_amount,
                    join_status=BankJoinStatus.AMBIGUOUS_MATCH,
                    variance=(matching_txns[0].credit_amount or 0) - s.amount,
                    notes=f"Multiple bank transactions ({len(matching_txns)}) found with identical UTR {s_utr}.",
                )
            else:
                b_txn = matching_txns[0]
                b_credit = b_txn.credit_amount or 0
                variance = b_credit - s.amount

                # Calculate clearing delay
                clearing_delay_hours = None
                s_time = s.settled_at or s.created_at
                b_time = b_txn.value_date or b_txn.transaction_date
                if s_time and b_time:
                    clearing_delay_hours = (b_time - s_time).total_seconds() / 3600.0

                if variance == 0:
                    if s.recon_status.value == "PENDING_BANK_CREDIT" or (clearing_delay_hours and clearing_delay_hours > 24.0 and s.recon_status.value != "MATCHED"):
                        join_status = BankJoinStatus.DELAYED_BANK_CREDIT
                    else:
                        join_status = BankJoinStatus.EXACT_UTR_MATCH
                else:
                    join_status = BankJoinStatus.AMOUNT_MISMATCH

                results[s.id] = BankJoinResult(
                    settlement_id=s.id,
                    utr=s_utr,
                    settlement_amount=s.amount,
                    bank_txn=b_txn,
                    bank_amount=b_credit,
                    join_status=join_status,
                    variance=variance,
                    clearing_delay_hours=clearing_delay_hours,
                    notes=f"Matched UTR {s_utr} with clearing delay of {clearing_delay_hours:.1f}h." if clearing_delay_hours is not None else None,
                )

        return results
