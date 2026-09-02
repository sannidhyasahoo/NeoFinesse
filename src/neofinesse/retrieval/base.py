from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.models.base import ProvenanceReference


class RetrievalStrategy(str, Enum):
    DIRECT_ID = "DIRECT_ID"
    ATTRIBUTE = "ATTRIBUTE"
    RELATIONSHIP = "RELATIONSHIP"
    TYPED_PROVENANCE = "TYPED_PROVENANCE"
    TEMPORAL_RELATIONSHIP = "TEMPORAL_RELATIONSHIP"
    UPI_EVENT = "UPI_EVENT"


class InvestigationTaskCategory(str, Enum):
    SETTLEMENT_RCA = "SETTLEMENT_RCA"
    UPI_STATE_INVESTIGATION = "UPI_STATE_INVESTIGATION"
    BANK_SETTLEMENT_STATE = "BANK_SETTLEMENT_STATE"


class TemporalRetrievalStatus(str, Enum):
    TEMPORALLY_VALID = "TEMPORALLY_VALID"
    OUTSIDE_WINDOW = "OUTSIDE_WINDOW"
    MISSING_TIMESTAMP = "MISSING_TIMESTAMP"
    NOT_EVALUATED = "NOT_EVALUATED"


class EvidenceCandidate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    candidate_id: str
    entity_type: str  # payment, refund, dispute, adjustment, transfer, upi_transaction, settlement_line
    entity_id: str
    amount: int  # Gross amount in paise
    net_financial_effect: Optional[int] = None  # Signed contribution in paise
    relationship_path: str
    temporal_status: TemporalRetrievalStatus = TemporalRetrievalStatus.NOT_EVALUATED
    timestamp: Optional[datetime] = None
    provenance: Optional[ProvenanceReference] = None
    is_provenance_complete: bool = False
    is_decoy: bool = False
    identity_confidence: str = "HIGH"  # HIGH, MEDIUM, LOW
    supporting_events: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_metadata: Dict[str, Any] = Field(default_factory=dict)


class RejectedEvidenceCandidate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    candidate_id: str
    entity_type: str
    entity_id: str
    amount: int
    rejection_strategy: RetrievalStrategy
    rejection_reason: str
    relationship_path: str
    timestamp: Optional[datetime] = None
    provenance: Optional[ProvenanceReference] = None


class RetrievalResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    case_id: str
    settlement_id: str
    strategy: RetrievalStrategy
    target_variance: int  # in paise
    candidates: List[EvidenceCandidate] = Field(default_factory=list)
    rejected_candidates: List[RejectedEvidenceCandidate] = Field(default_factory=list)
    retrieval_latency_ms: float = 0.0
    is_applicable: bool = True
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseRetrievalStrategy:
    """Abstract base class for evidence retrieval strategies."""

    strategy_name: RetrievalStrategy

    def is_strategy_applicable(self, task_category: InvestigationTaskCategory) -> bool:
        """Determines if this strategy is intended for the specified task category."""
        if self.strategy_name == RetrievalStrategy.UPI_EVENT:
            return task_category == InvestigationTaskCategory.UPI_STATE_INVESTIGATION
        else:
            return task_category in (
                InvestigationTaskCategory.SETTLEMENT_RCA,
                InvestigationTaskCategory.BANK_SETTLEMENT_STATE,
            )

    def retrieve(
        self,
        case_id: str,
        settlement_id: str,
        target_variance: int,
        dataset: Any,
        task_category: InvestigationTaskCategory = InvestigationTaskCategory.SETTLEMENT_RCA,
    ) -> RetrievalResult:
        raise NotImplementedError
