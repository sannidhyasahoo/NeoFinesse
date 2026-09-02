import uuid
from datetime import datetime
from typing import List, Optional

from neofinesse.investigation.models import (
    ConstraintStatus,
    Hypothesis,
    HypothesisStatus,
    InvestigationAuditRecord,
    InvestigationStatus,
)


class InvestigationAuditBuilder:
    """Constructs comprehensive, provenance-backed audit records for investigation cases."""

    @staticmethod
    def build_audit_record(
        case_id: str,
        settlement_id: str,
        target_variance: int,
        final_status: InvestigationStatus,
        winning_hypothesis: Optional[Hypothesis],
        rejected_hypotheses: List[Hypothesis],
    ) -> InvestigationAuditRecord:
        audit_id = f"AUD-INV-{case_id}-{uuid.uuid4().hex[:6]}"

        passed_constraints = []
        failed_constraints = []
        supporting_provenance = []
        counterfactual_notes = ""

        if winning_hypothesis:
            explained = winning_hypothesis.explained_amount
            unexplained = winning_hypothesis.unexplained_amount
            winning_id = winning_hypothesis.hypothesis_id

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
                        "source_file": prov.source_file if prov else None,
                        "source_sheet": prov.source_sheet if prov else None,
                        "source_row": prov.source_row if prov else None,
                        "source_columns": prov.source_columns if prov else None,
                        "source_hash": prov.source_hash if prov else None,
                        "record_hash": prov.record_hash if prov else None,
                    }
                )

            if len(winning_hypothesis.candidate_evidence) == 1:
                cand = winning_hypothesis.candidate_evidence[0]
                counterfactual_notes = (
                    f"Counterfactual Analysis: Excluding primary candidate '{cand.entity_id}' restores the unexplained variance to ₹{abs(target_variance)/100:.2f}."
                )
            elif len(winning_hypothesis.candidate_evidence) > 1:
                names = ", ".join(c.entity_id for c in winning_hypothesis.candidate_evidence)
                counterfactual_notes = (
                    f"Counterfactual Analysis: Joint composite attribution over ({names}). Removing any constituent event leaves a corresponding unexplained residual."
                )

            summary = f"Investigation concluded with status {final_status.value}. Hypothesis '{winning_id}' verified at {winning_hypothesis.evidence_level.value}."
        else:
            explained = 0
            unexplained = target_variance
            winning_id = None
            summary = f"Investigation concluded with status {final_status.value}. No candidate hypothesis satisfied all mandatory financial and relational constraints."
            counterfactual_notes = "No valid causal candidates identified. Full variance remains unexplained."

        # Compile rejection reasons
        rejected_reasons = []
        for rh in rejected_hypotheses:
            failed_reasons = [
                f"{cr.constraint_name} ({cr.reason})"
                for cr in rh.constraint_results
                if cr.status == ConstraintStatus.FAIL
            ]
            rejected_reasons.append(
                {
                    "hypothesis_id": rh.hypothesis_id,
                    "cause_type": rh.cause_type.value,
                    "evidence_ids": ", ".join(rh.evidence_ids),
                    "rejection_reasons": "; ".join(failed_reasons) if failed_reasons else "Failed constraint verification",
                }
            )

        return InvestigationAuditRecord(
            audit_id=audit_id,
            case_id=case_id,
            settlement_id=settlement_id,
            target_variance_paise=target_variance,
            target_variance_inr=target_variance / 100.0,
            final_status=final_status,
            summary=summary,
            winning_hypothesis_id=winning_id,
            explained_amount_paise=explained,
            unexplained_amount_paise=unexplained,
            passed_constraints=passed_constraints,
            failed_constraints=failed_constraints,
            supporting_evidence_provenance=supporting_provenance,
            rejected_hypotheses_reasons=rejected_reasons,
            counterfactual_notes=counterfactual_notes,
            timestamp=datetime.now(),
        )
