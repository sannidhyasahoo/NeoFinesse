from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ScenarioType(str, Enum):
    REFUND_VARIANCE = "VAR-001_REFUND_VARIANCE"
    SAME_AMOUNT_DECOY = "VAR-002_SAME_AMOUNT_DECOY"
    PARTIAL_EXPLANATION = "VAR-003_PARTIAL_EXPLANATION"
    MULTIPLE_EVENT_EXPLANATION = "VAR-004_MULTIPLE_EVENT_EXPLANATION"
    UPI_LATE_SUCCESS = "VAR-005_UPI_LATE_SUCCESS"
    UPI_DEBIT_REVERSAL = "VAR-006_UPI_DEBIT_REVERSAL"
    DELAYED_BANK_CREDIT = "VAR-007_DELAYED_BANK_CREDIT"
    WRONG_DATE_DECOY = "VAR-008_WRONG_DATE_DECOY"
    WRONG_PAYMENT_DECOY = "VAR-009_WRONG_PAYMENT_DECOY"
    COMPLETELY_UNEXPLAINED = "VAR-010_COMPLETELY_UNEXPLAINED"


class ExpectedOutcome(str, Enum):
    RESOLVED = "RESOLVED"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    VALID_DELAYED_CREDIT = "VALID_DELAYED_CREDIT"
    ESCALATE = "ESCALATE"


class GroundTruthCause(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_type: str = Field(description="Type of causing entity (refund, dispute, adjustment, payment, upi)")
    entity_id: str = Field(description="Identifier of the causing entity")
    settlement_line_id: Optional[str] = Field(default=None, description="Linked SettlementLine ID if present")
    amount: int = Field(description="Financial contribution in paise")


class GroundTruthDecoy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decoy_type: str = Field(description="Reason why this is a decoy (same_amount, wrong_date, wrong_payment)")
    entity_type: str = Field(description="Type of decoy entity")
    entity_id: str = Field(description="Identifier of decoy entity")
    amount: int = Field(description="Amount of decoy in paise")
    rejection_reason: str = Field(description="Why the investigator must reject this candidate")


class CaseGroundTruth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(description="Case identifier (e.g. CASE-001)")
    settlement_id: str = Field(description="Target settlement batch ID")
    scenario: ScenarioType = Field(description="Scenario category")
    expected_variance: int = Field(description="Expected variance amount in paise (expected - actual)")
    true_causes: List[GroundTruthCause] = Field(default_factory=list, description="Verified true cause entities")
    decoys: List[GroundTruthDecoy] = Field(default_factory=list, description="Decoys injected to test investigator robustness")
    explained_amount: int = Field(description="Portion of variance provably explained in paise")
    unexplained_amount: int = Field(description="Portion of variance remaining unexplained in paise")
    expected_outcome: ExpectedOutcome = Field(description="Expected final investigation status")
    notes: Optional[str] = Field(default=None, description="Human description of injected financial situation")
