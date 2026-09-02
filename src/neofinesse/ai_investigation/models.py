from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.investigation.models import CauseType, Hypothesis, InvestigationAuditRecord, InvestigationStatus
from neofinesse.models.base import EvidenceLevel


class ConflictType(str, Enum):
    TIMING_MISMATCH = "TIMING_MISMATCH"
    MEMBERSHIP_MISMATCH = "MEMBERSHIP_MISMATCH"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    STATE_MISMATCH = "STATE_MISMATCH"
    PROVENANCE_MISMATCH = "PROVENANCE_MISMATCH"
    OTHER = "OTHER"


class ConflictItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conflict_id: str
    conflict_type: ConflictType
    evidence_ids: List[str] = Field(description="IDs of contradictory evidence items")
    description: str = Field(description="Explanation of the contradiction")


class MissingEvidenceCriticality(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MissingEvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    missing_id: str
    entity_type: str = Field(description="Type of entity missing (e.g. refund, reversal, bank_credit)")
    criticality: MissingEvidenceCriticality = Field(default=MissingEvidenceCriticality.HIGH)
    description: str = Field(description="Why this evidence is necessary for closure")
    suggested_source: Optional[str] = Field(default=None, description="Where this evidence might be found")


class AIHypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hypothesis_id: str
    cause_type: CauseType
    evidence_ids: List[str] = Field(description="Must reference valid evidence IDs in the evidence pack")
    claimed_explained_amount: int = Field(description="LLM's claimed explained amount in integer paise")
    recalculated_explained_amount: Optional[int] = Field(default=None, description="Independently recalculated amount in paise")
    reasoning: str = Field(description="Detailed financial reasoning referencing specific evidence IDs")
    missing_evidence: List[MissingEvidenceItem] = Field(default_factory=list)
    conflicts: List[ConflictItem] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)


class AIInvestigationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    hypotheses: List[AIHypothesis] = Field(default_factory=list)
    recommended_hypothesis_id: Optional[str] = Field(default=None, description="Recommended hypothesis ID or None for escalation")
    investigation_summary: str
    confidence_assessment: str = Field(default="MEDIUM", description="HIGH, MEDIUM, LOW")


class AIRejectionReason(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hypothesis_id: str
    rejection_stage: str = Field(description="SCHEMA_VALIDATION, HALLUCINATION_CHECK, ARITHMETIC_CHECK, VERIFIER_CONSTRAINTS")
    reasons: List[str]


class VerifiedAIInvestigationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    settlement_id: str
    target_variance: int  # in paise
    ai_raw_response: Optional[str] = None
    ai_response: Optional[AIInvestigationResponse] = None
    validated_hypotheses: List[Hypothesis] = Field(default_factory=list)
    rejected_ai_hypotheses: List[AIRejectionReason] = Field(default_factory=list)
    winning_hypothesis: Optional[Hypothesis] = None
    final_status: InvestigationStatus
    explained_amount: int  # in paise
    unexplained_amount: int  # in paise
    audit_record: InvestigationAuditRecord
    ai_helped: bool = False
    verifier_corrected_ai: bool = False
    conflicts_detected: List[ConflictItem] = Field(default_factory=list)
    missing_evidence_detected: List[MissingEvidenceItem] = Field(default_factory=list)
    llm_latency_ms: float = 0.0
    verification_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
