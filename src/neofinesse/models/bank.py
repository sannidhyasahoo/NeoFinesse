from datetime import datetime
from typing import Optional
from pydantic import Field

from neofinesse.models.base import BaseDomainModel


class BankTransaction(BaseDomainModel):
    bank_txn_id: str = Field(description="Bank transaction identifier (e.g. bank_XXXX)")
    utr: Optional[str] = Field(default=None, description="Bank Unique Transaction Reference")
    credit_amount: Optional[int] = Field(default=None, ge=0, description="Credit amount in paise")
    debit_amount: Optional[int] = Field(default=None, ge=0, description="Debit amount in paise")
    balance: Optional[int] = Field(default=None, description="Account balance after transaction in paise")
    value_date: datetime = Field(description="Value date")
    transaction_date: datetime = Field(description="Posting date")
    raw_description: str = Field(description="Raw bank statement narration text")
    parsed_utr: Optional[str] = Field(default=None, description="Parsed UTR extracted from narration")
    account_number: str = Field(default="ACC9988776655", description="Bank account identifier")
