import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from neofinesse.agentic_investigation.state import InvestigationState
from neofinesse.investigation.models import (
    ConstraintStatus,
    Hypothesis,
    HypothesisStatus,
    InvestigationAuditRecord,
    InvestigationStatus,
)


class AgenticAuditBuilder:
    """Builds full provenance-preserving audit trails for multi-round agentic investigations."""

    @staticmethod
    def build_agentic_audit_record(
        state: InvestigationState,
        winning_hypothesis: Optional[Hypothesis],
        final_status: InvestigationStatus,
        explained_amount: int,
        unexplained_amount: int,
        rejected_hypotheses: List[Hypothesis],
    ) -> InvestigationAuditRecord:
        audit_id = f"AUD-AGT-{state.case_id}-{uuid.uuid4().hex[:6]}"

        passed_constraints: List[str] = []
        failed_constraints: List[str] = []
        supporting_provenance: List[Dict[str, Any]] = []
        counterfactual_notes = ""

        if winning_hypothesis:
            for cr in winning_hypothesis.constraint_results:
                if cr.status in (ConstraintStatus.PASS, ConstraintStatus.WARN):
                    passed_constraints.append(f"{cr.constraint_name}: {cr.reason}")
                else:
                    failed_constraints.append(f"{cr.constraint_name}: {cr.reason}")

            for c in winning_hypothesis.candidate_evidence:
                prov = c.provenance
                supporting_provenance.append(
                    {
                        "candidate_id": c.candidate_id,
                        "entity_type": c.entity_type,
                        "entity_id": c.entity_id,
                        "amount_paise": c.amount,
                        "relationship_path": c.relationship_path,
                        "source_file": prov.source_file if prov else "unknown_file",
                        "source_row": prov.source_row if prov else 0,
                        "source_hash": prov.source_hash if prov else "MISSING_HASH",
                        "record_hash": prov.record_hash if prov else "MISSING_HASH",
                    }
                )

            if len(winning_hypothesis.candidate_evidence) > 1:
                counterfactual_notes = (
                    f"Agentic Multi-Event Verification: Verified across {len(winning_hypothesis.candidate_evidence)} "
                    f"constituent events across {state.round_number} rounds. Excluding any constituent event restores residual variance."
                )
            else:
                counterfactual_notes = (
                    f"Agentic Single-Event Verification: Verified across {state.round_number} rounds. "
                    f"Excluding primary candidate restores full unexplained variance."
                )
        else:
            counterfactual_notes = (
                f"Agentic Investigation Escalation: Concluded after {state.round_number} rounds and "
                f"{len(state.completed_requests)} tool calls. No valid hypothesis satisfied all financial and relational constraints."
            )

        # Build structured rejection rationales
        rejection_records: List[Dict[str, Any]] = []
        for rh in rejected_hypotheses:
            failed_reasons = [
                f"{cr.constraint_name} ({cr.reason})"
                for cr in rh.constraint_results
                if cr.status == ConstraintStatus.FAIL
            ]
            rejection_records.append(
                {
                    "hypothesis_id": rh.hypothesis_id,
                    "cause_type": rh.cause_type.value,
                    "evidence_ids": ",".join(rh.evidence_ids),
                    "rejection_reasons": "; ".join(failed_reasons) if failed_reasons else "Failed constraint verification",
                }
            )

        # Add explicit round history into summary
        summary = (
            f"Agentic Investigation completed in {state.round_number} round(s) with {len(state.completed_requests)} tool call(s). "
            f"Final Outcome: {final_status.value} (Explained: ₹{explained_amount/100:.2f}, Unexplained: ₹{unexplained_amount/100:.2f})."
        )

        return InvestigationAuditRecord(
            audit_id=audit_id,
            case_id=state.case_id,
            settlement_id=state.settlement_id,
            target_variance_paise=state.target_variance,
            target_variance_inr=state.target_variance / 100.0,
            final_status=final_status,
            summary=summary,
            winning_hypothesis_id=winning_hypothesis.hypothesis_id if winning_hypothesis else None,
            explained_amount_paise=explained_amount,
            unexplained_amount_paise=unexplained_amount,
            passed_constraints=passed_constraints,
            failed_constraints=failed_constraints,
            supporting_evidence_provenance=supporting_provenance,
            rejected_hypotheses_reasons=rejection_records,
            counterfactual_notes=counterfactual_notes,
            timestamp=datetime.now(),
        )
