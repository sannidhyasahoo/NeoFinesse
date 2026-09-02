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


class TemporalRetrievalStatus(str, Enum):
    TEMPORALLY_VALID = "TEMPORALLY_VALID"
    OUTSIDE_WINDOW = "OUTSIDE_WINDOW"
    MISSING_TIMESTAMP = "MISSING_TIMESTAMP"
    NOT_EVALUATED = "NOT_EVALUATED"


class EvidenceCandidate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    candidate_id: str
    entity_type: str  # payment, refund, dispute, adjustment, transfer, upi_transaction, upi_event, settlement_line
    entity_id: str
    amount: int  # Gross amount in paise
    net_financial_effect: Optional[int] = None  # Signed contribution in paise
    relationship_path: str
    temporal_status: TemporalRetrievalStatus = TemporalRetrievalStatus.NOT_EVALUATED
    timestamp: Optional[datetime] = None
    provenance: Optional[ProvenanceReference] = None
    is_provenance_complete: bool = False
    is_decoy: bool = False
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
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseRetrievalStrategy:
    """Abstract base class for evidence retrieval strategies."""

    strategy_name: RetrievalStrategy

    def retrieve(self, case_id: str, settlement_id: str, target_variance: int, dataset: Any) -> RetrievalResult:
        raise NotImplementedError
