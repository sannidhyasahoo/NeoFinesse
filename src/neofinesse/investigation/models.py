from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.models.base import EvidenceLevel, ProvenanceReference
from neofinesse.retrieval.base import EvidenceCandidate, InvestigationTaskCategory


class InvestigationStatus(str, Enum):
    RESOLVED = "RESOLVED"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    VALID_DELAYED_CREDIT = "VALID_DELAYED_CREDIT"
    ESCALATE = "ESCALATE"


class CauseType(str, Enum):
    REFUND = "REFUND"
    CHARGEBACK = "CHARGEBACK"
    DISPUTE = "DISPUTE"
    ADJUSTMENT = "ADJUSTMENT"
    DELAYED_SETTLEMENT = "DELAYED_SETTLEMENT"
    UPI_STATE = "UPI_STATE"
    COMPOSITE = "COMPOSITE"
    UNKNOWN = "UNKNOWN"


class ConstraintStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    WARN = "WARN"


class ConstraintResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    constraint_name: str
    status: ConstraintStatus
    expected: Any
    observed: Any
    evidence_ids: List[str] = Field(default_factory=list)
    reason: str


class HypothesisStatus(str, Enum):
    PROPOSED = "PROPOSED"
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    REJECTED = "REJECTED"


class Hypothesis(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    hypothesis_id: str
    case_id: str
    cause_type: CauseType
    evidence_ids: List[str] = Field(default_factory=list)
    candidate_evidence: List[EvidenceCandidate] = Field(default_factory=list)
    target_variance: int  # in paise
    explained_amount: int  # in paise
    unexplained_amount: int  # in paise
    constraint_results: List[ConstraintResult] = Field(default_factory=list)
    evidence_level: EvidenceLevel = EvidenceLevel.L0
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    explanation: str
    counterfactual_residual: Optional[int] = None
    hypothesis_metadata: Dict[str, Any] = Field(default_factory=dict)


class InvestigationAuditRecord(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    audit_id: str
    case_id: str
    settlement_id: str
    target_variance_paise: int
    target_variance_inr: float
    final_status: InvestigationStatus
    summary: str
    winning_hypothesis_id: Optional[str] = None
    explained_amount_paise: int
    unexplained_amount_paise: int
    passed_constraints: List[str] = Field(default_factory=list)
    failed_constraints: List[str] = Field(default_factory=list)
    supporting_evidence_provenance: List[Dict[str, Any]] = Field(default_factory=list)
    rejected_hypotheses_reasons: List[Dict[str, str]] = Field(default_factory=list)
    counterfactual_notes: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class InvestigationResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    case_id: str
    settlement_id: str
    target_variance: int  # in paise
    task_category: InvestigationTaskCategory
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    winning_hypothesis: Optional[Hypothesis] = None
    explained_amount: int = 0  # in paise
    unexplained_amount: int = 0  # in paise
    final_status: InvestigationStatus
    rejected_hypotheses: List[Hypothesis] = Field(default_factory=list)
    audit_record: Optional[InvestigationAuditRecord] = None
    investigation_latency_ms: float = 0.0
