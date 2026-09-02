from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.models.base import EvidenceLevel, ProvenanceReference
from neofinesse.reconciliation.solver import RejectedCandidate, VerifiedCause


class CaseAuditRecord(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    case_id: str
    settlement_id: str
    expected_amount: int  # Expected from Σ SettlementLine.net_amount (paise)
    actual_amount: int    # Actual provider settled amount (paise)
    bank_amount: Optional[int] = None  # Actual bank credit amount (paise)
    variance_amount: int  # expected_amount - actual_amount (paise)
    status: str           # MATCHED, RESOLVED, PARTIALLY_RESOLVED, VALID_DELAYED_CREDIT, ESCALATE
    explained_amount: int
    unexplained_amount: int
    verified_causes: List[VerifiedCause] = Field(default_factory=list)
    rejected_candidates: List[RejectedCandidate] = Field(default_factory=list)
    evidence_level: EvidenceLevel
    escalation_reason: Optional[str] = None
    utr: Optional[str] = None
    bank_credit_matched: bool = False
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None


class AuditRecordBuilder:
    """Builds comprehensive, auditable investigation records with full cell/file provenance citations."""

    @staticmethod
    def build_case_record(
        case_id: str,
        settlement_id: str,
        expected_amount: int,
        actual_amount: int,
        bank_amount: Optional[int],
        variance_amount: int,
        status: str,
        explained_amount: int,
        unexplained_amount: int,
        verified_causes: List[VerifiedCause],
        rejected_candidates: List[RejectedCandidate],
        evidence_level: EvidenceLevel,
        utr: Optional[str],
        bank_credit_matched: bool,
        escalation_reason: Optional[str] = None,
        audit_trail: Optional[List[Dict[str, Any]]] = None,
    ) -> CaseAuditRecord:
        resolved_at = datetime.now() if status in ("MATCHED", "RESOLVED", "VALID_DELAYED_CREDIT") else None

        trail = audit_trail or []
        # Add summary trail entry
        trail.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": "CASE_CLASSIFICATION",
                "status": status,
                "evidence_level": evidence_level.value,
                "verified_cause_count": len(verified_causes),
                "rejected_candidate_count": len(rejected_candidates),
                "explained_amount_inr": explained_amount / 100.0,
                "unexplained_amount_inr": unexplained_amount / 100.0,
            }
        )

        return CaseAuditRecord(
            case_id=case_id,
            settlement_id=settlement_id,
            expected_amount=expected_amount,
            actual_amount=actual_amount,
            bank_amount=bank_amount,
            variance_amount=variance_amount,
            status=status,
            explained_amount=explained_amount,
            unexplained_amount=unexplained_amount,
            verified_causes=verified_causes,
            rejected_candidates=rejected_candidates,
            evidence_level=evidence_level,
            escalation_reason=escalation_reason,
            utr=utr,
            bank_credit_matched=bank_credit_matched,
            audit_trail=trail,
            created_at=datetime.now(),
            resolved_at=resolved_at,
        )
