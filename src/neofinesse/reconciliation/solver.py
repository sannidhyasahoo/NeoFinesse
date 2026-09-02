from itertools import combinations
from typing import List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.models.base import EvidenceLevel, ProvenanceReference
from neofinesse.models.settlement import Settlement
from neofinesse.reconciliation.candidates import CandidateEvent
from neofinesse.reconciliation.temporal import TemporalConstraintFilter, TemporalStatus


class VerifiedCause(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    entity_type: str
    entity_id: str
    settlement_line_id: Optional[str] = None
    amount: int
    net_financial_effect: int
    relationship_path: str
    evidence_level: EvidenceLevel
    provenance: Optional[ProvenanceReference] = None
    verification_chain: List[str] = Field(default_factory=list)


class RejectedCandidate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    candidate_id: str
    entity_type: str
    entity_id: str
    amount: int
    net_financial_effect: int
    rejection_stage: str  # SETTLEMENT_RELEVANCE, RELATIONSHIP, TEMPORAL, FINANCIAL_EFFECT, MONETARY
    rejection_reason: str
    provenance: Optional[ProvenanceReference] = None


class AttributionResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    target_variance: int
    explained_amount: int
    unexplained_amount: int
    verified_causes: List[VerifiedCause] = Field(default_factory=list)
    rejected_candidates: List[RejectedCandidate] = Field(default_factory=list)
    solver_status: str  # RESOLVED, PARTIALLY_RESOLVED, ESCALATE
    evidence_level: EvidenceLevel


class MultiConstraintAttributionSolver:
    """Deterministic 5-stage attribution solver finding verified causal events explaining settlement variance."""

    def __init__(self, temporal_filter: Optional[TemporalConstraintFilter] = None):
        self.temporal_filter = temporal_filter or TemporalConstraintFilter()

    def solve(
        self,
        settlement: Settlement,
        target_variance: int,
        candidates: List[CandidateEvent],
    ) -> AttributionResult:
        """Applies 5-stage multi-constraint attribution on candidate set."""
        rejected_candidates: List[RejectedCandidate] = []
        valid_candidates: List[CandidateEvent] = []

        # If target variance is 0, check if this is a verified baseline / matched case
        if target_variance == 0:
            return AttributionResult(
                target_variance=0,
                explained_amount=0,
                unexplained_amount=0,
                verified_causes=[],
                rejected_candidates=[],
                solver_status="RESOLVED",
                evidence_level=EvidenceLevel.L5,
            )

        # Stage 1 & 2: Settlement Relevance & Explicit Relationship Validation
        for cand in candidates:
            # Check explicit relationship to this settlement batch
            is_linked = (
                cand.is_settlement_constituent
                or (cand.settlement_id is not None and cand.settlement_id == settlement.id)
            )

            # Rejection 1: Belongs to another settlement batch
            if cand.settlement_id and cand.settlement_id != settlement.id and not cand.is_settlement_constituent:
                rejected_candidates.append(
                    RejectedCandidate(
                        candidate_id=cand.candidate_id,
                        entity_type=cand.entity_type,
                        entity_id=cand.entity_id,
                        amount=cand.amount,
                        net_financial_effect=cand.net_financial_effect,
                        rejection_stage="SETTLEMENT_RELEVANCE",
                        rejection_reason=f"Event belongs to another settlement batch ({cand.settlement_id}), not target settlement ({settlement.id}).",
                        provenance=cand.provenance,
                    )
                )
                continue

            # Rejection 2: Unrelated event with no relational connection to target batch
            if not is_linked:
                rejected_candidates.append(
                    RejectedCandidate(
                        candidate_id=cand.candidate_id,
                        entity_type=cand.entity_type,
                        entity_id=cand.entity_id,
                        amount=cand.amount,
                        net_financial_effect=cand.net_financial_effect,
                        rejection_stage="RELATIONSHIP",
                        rejection_reason="No explicit foreign-key or batch relationship links this event to the target settlement.",
                        provenance=cand.provenance,
                    )
                )
                continue

            # Stage 3: Temporal Validation
            is_valid_time, time_status, time_reason = self.temporal_filter.validate_candidate_timing(
                cand, settlement
            )
            if not is_valid_time:
                rejected_candidates.append(
                    RejectedCandidate(
                        candidate_id=cand.candidate_id,
                        entity_type=cand.entity_type,
                        entity_id=cand.entity_id,
                        amount=cand.amount,
                        net_financial_effect=cand.net_financial_effect,
                        rejection_stage="TEMPORAL",
                        rejection_reason=time_reason,
                        provenance=cand.provenance,
                    )
                )
                continue

            # Stage 4: Valid Non-Zero Financial Effect Validation
            if cand.net_financial_effect == 0:
                rejected_candidates.append(
                    RejectedCandidate(
                        candidate_id=cand.candidate_id,
                        entity_type=cand.entity_type,
                        entity_id=cand.entity_id,
                        amount=cand.amount,
                        net_financial_effect=cand.net_financial_effect,
                        rejection_stage="FINANCIAL_EFFECT",
                        rejection_reason="Event has net financial effect of 0 paise (e.g. reversed debit / non-deduction); cannot explain deficit.",
                        provenance=cand.provenance,
                    )
                )
                continue

            valid_candidates.append(cand)

        # Stage 5: Monetary Consistency (Subset-Sum Exact Matching)
        target = target_variance  # e.g. -200000, -250000, -100000, 200000
        best_subset: List[CandidateEvent] = []
        best_sum = 0
        found_exact = False

        # Try exact single-event match first
        for cand in valid_candidates:
            if cand.net_financial_effect == target or cand.amount == abs(target) or -cand.amount == target:
                best_subset = [cand]
                best_sum = cand.net_financial_effect if cand.net_financial_effect != 0 else -cand.amount
                found_exact = True
                break

        # Try multi-event combinations (up to size 4)
        if not found_exact and len(valid_candidates) > 1:
            for k in range(2, min(5, len(valid_candidates) + 1)):
                for combo in combinations(valid_candidates, k):
                    combo_sum = sum(c.net_financial_effect for c in combo)
                    if combo_sum == target or abs(combo_sum) == abs(target):
                        best_subset = list(combo)
                        best_sum = combo_sum
                        found_exact = True
                        break
                if found_exact:
                    break

        # If no exact match, find maximal valid constituent subset (Partial explanation)
        if not found_exact and valid_candidates:
            constituent_cands = [c for c in valid_candidates if c.is_settlement_constituent or c.payment_id]
            if constituent_cands:
                best_subset = constituent_cands
                best_sum = sum(c.net_financial_effect for c in constituent_cands)

        # Build VerifiedCauses
        verified_causes: List[VerifiedCause] = []
        for c in best_subset:
            level = EvidenceLevel.L4 if found_exact else EvidenceLevel.L3
            v_chain = [
                f"Relationship: {c.relationship_path}",
                f"Temporal: timestamp {c.timestamp.isoformat()} validated before cutoff",
                f"Financial: net effect {c.net_financial_effect} paise verified",
            ]
            if c.is_settlement_constituent:
                v_chain.append(f"SettlementLine {c.settlement_line_id} confirmed in batch {settlement.id}")

            verified_causes.append(
                VerifiedCause(
                    entity_type=c.entity_type,
                    entity_id=c.entity_id,
                    settlement_line_id=c.settlement_line_id,
                    amount=c.amount,
                    net_financial_effect=c.net_financial_effect,
                    relationship_path=c.relationship_path,
                    evidence_level=level,
                    provenance=c.provenance,
                    verification_chain=v_chain,
                )
            )

        # Unused valid candidates are recorded
        used_ids = {c.entity_id for c in best_subset}
        for c in valid_candidates:
            if c.entity_id not in used_ids:
                rejected_candidates.append(
                    RejectedCandidate(
                        candidate_id=c.candidate_id,
                        entity_type=c.entity_type,
                        entity_id=c.entity_id,
                        amount=c.amount,
                        net_financial_effect=c.net_financial_effect,
                        rejection_stage="MONETARY",
                        rejection_reason=f"Candidate amount ({c.net_financial_effect} paise) does not fit target variance subset-sum ({target} paise).",
                        provenance=c.provenance,
                    )
                )

        explained_amount = abs(best_sum)
        if found_exact:
            unexplained_amount = 0
            solver_status = "RESOLVED"
            overall_level = EvidenceLevel.L4
        elif verified_causes:
            # Partial explanation
            unexplained_amount = abs(abs(target) - explained_amount) if abs(target) != explained_amount else abs(target)
            solver_status = "PARTIALLY_RESOLVED"
            overall_level = EvidenceLevel.L3
        else:
            solver_status = "ESCALATE"
            overall_level = EvidenceLevel.L0
            explained_amount = 0
            unexplained_amount = abs(target)

        return AttributionResult(
            target_variance=target,
            explained_amount=explained_amount,
            unexplained_amount=unexplained_amount,
            verified_causes=verified_causes,
            rejected_candidates=rejected_candidates,
            solver_status=solver_status,
            evidence_level=overall_level,
        )
