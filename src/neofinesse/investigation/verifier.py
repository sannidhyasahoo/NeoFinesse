from typing import List

from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.investigation.constraints import (
    MonetaryConstraint,
    ProvenanceConstraint,
    RelationshipConstraint,
    StateConstraint,
    TemporalConstraint,
)
from neofinesse.investigation.hypothesis import HypothesisBuilder
from neofinesse.investigation.models import (
    ConstraintResult,
    ConstraintStatus,
    Hypothesis,
    HypothesisStatus,
)
from neofinesse.models.base import EvidenceLevel


class HypothesisVerifier:
    """Evaluates candidate hypotheses against deterministic financial and operational constraints."""

    @staticmethod
    def verify(
        hypothesis: Hypothesis,
        settlement_id: str,
        target_variance: int,
        dataset: IngestedDataset,
    ) -> Hypothesis:
        results: List[ConstraintResult] = []

        # 1. Run Relationship Constraint
        rel_res = RelationshipConstraint.evaluate(hypothesis, settlement_id, dataset)
        results.append(rel_res)

        # 2. Run Temporal Constraint
        temp_res = TemporalConstraint.evaluate(hypothesis, settlement_id, dataset)
        results.append(temp_res)

        # 3. Run State Constraint
        state_res = StateConstraint.evaluate(hypothesis, dataset)
        results.append(state_res)

        # 4. Run Provenance Constraint
        prov_res = ProvenanceConstraint.evaluate(hypothesis)
        results.append(prov_res)

        # 5. Run Monetary Constraint
        mon_res = MonetaryConstraint.evaluate(hypothesis, target_variance)
        results.append(mon_res)

        # Evaluate overall pass/fail status
        mandatory_non_monetary_passed = (
            rel_res.status == ConstraintStatus.PASS
            and temp_res.status == ConstraintStatus.PASS
            and state_res.status == ConstraintStatus.PASS
        )

        has_provenance = prov_res.status == ConstraintStatus.PASS
        monetary_exact = mon_res.status == ConstraintStatus.PASS
        monetary_partial = mon_res.status == ConstraintStatus.WARN

        # Compute counterfactual residual
        counterfactual = HypothesisBuilder.compute_counterfactual_residual(hypothesis)

        # Determine evidence level and status
        if mandatory_non_monetary_passed and monetary_exact:
            evidence_lvl = EvidenceLevel.L5 if has_provenance else EvidenceLevel.L4
            status = HypothesisStatus.VERIFIED
        elif mandatory_non_monetary_passed and monetary_partial:
            evidence_lvl = EvidenceLevel.L3
            status = HypothesisStatus.PARTIALLY_VERIFIED
        else:
            evidence_lvl = EvidenceLevel.L1 if rel_res.status == ConstraintStatus.PASS else EvidenceLevel.L0
            status = HypothesisStatus.REJECTED

        # Update hypothesis
        hypothesis.constraint_results = results
        hypothesis.evidence_level = evidence_lvl
        hypothesis.status = status
        hypothesis.counterfactual_residual = counterfactual

        return hypothesis
