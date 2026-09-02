import statistics
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.models.ground_truth import CaseGroundTruth
from neofinesse.retrieval.base import (
    InvestigationTaskCategory,
    RetrievalResult,
    RetrievalStrategy,
)


def get_scenario_task_category(scenario_value: str) -> InvestigationTaskCategory:
    """Classifies ground truth scenario into its primary investigation task category."""
    if "UPI" in scenario_value:
        return InvestigationTaskCategory.UPI_STATE_INVESTIGATION
    elif "DELAYED_BANK_CREDIT" in scenario_value:
        return InvestigationTaskCategory.BANK_SETTLEMENT_STATE
    else:
        return InvestigationTaskCategory.SETTLEMENT_RCA


class StrategyMetrics(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    strategy: RetrievalStrategy
    total_cases_evaluated: int
    applicable_cases: int
    na_cases: int
    true_causes_expected: int
    true_causes_retrieved: int
    evidence_recall_pct: Optional[float] = None
    total_candidates_retrieved: int
    true_candidates_count: int
    candidate_precision_pct: Optional[float] = None
    total_known_decoys: int
    decoys_rejected: int
    decoy_rejection_rate_pct: Optional[float] = None
    total_provenance_verified: int
    provenance_coverage_pct: Optional[float] = None
    avg_latency_ms: float = 0.0
    median_latency_ms: float = 0.0
    max_latency_ms: float = 0.0


class ScenarioEvaluationRow(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    scenario_id: str
    strategy: RetrievalStrategy
    task_category: InvestigationTaskCategory
    case_id: str
    settlement_id: str
    target_variance_inr: float
    is_applicable: bool = True
    true_causes_expected: int
    true_causes_retrieved: int
    recall_pct: Optional[float] = None
    candidates_retrieved: int
    precision_pct: Optional[float] = None
    decoys_present: int
    decoys_rejected: int
    decoy_rejection_pct: Optional[float] = None
    provenance_coverage_pct: Optional[float] = None
    latency_ms: float = 0.0
    notes: str = ""


class RetrievalEvaluator:
    """Evaluates retrieval results against Ground Truth with strict applicability and N/A semantics."""

    @staticmethod
    def evaluate_scenario(
        result: RetrievalResult, ground_truth: CaseGroundTruth
    ) -> ScenarioEvaluationRow:
        task_category = get_scenario_task_category(ground_truth.scenario.value)

        # Check if strategy is applicable to this task category
        is_applicable = result.is_applicable

        expected_cause_ids = {c.entity_id for c in ground_truth.true_causes}
        retrieved_ids = {c.entity_id for c in result.candidates}
        decoy_ids = {d.entity_id for d in ground_truth.decoys}

        # Check true causes retrieved
        true_retrieved = expected_cause_ids.intersection(retrieved_ids)

        if not is_applicable:
            return ScenarioEvaluationRow(
                scenario_id=ground_truth.scenario.value,
                strategy=result.strategy,
                task_category=task_category,
                case_id=result.case_id,
                settlement_id=result.settlement_id,
                target_variance_inr=result.target_variance / 100.0,
                is_applicable=False,
                true_causes_expected=len(expected_cause_ids),
                true_causes_retrieved=len(true_retrieved),
                recall_pct=None,
                candidates_retrieved=len(result.candidates),
                precision_pct=None,
                decoys_present=len(decoy_ids),
                decoys_rejected=0,
                decoy_rejection_pct=None,
                provenance_coverage_pct=None,
                latency_ms=result.retrieval_latency_ms,
                notes=f"Strategy {result.strategy.value} not applicable to {task_category.value}",
            )

        # 1. Evidence Recall: Only defined if expected causes > 0
        if len(expected_cause_ids) > 0:
            recall: Optional[float] = (len(true_retrieved) / len(expected_cause_ids)) * 100.0
        else:
            recall = None  # N/A

        # 2. Candidate Precision:
        if len(result.candidates) > 0:
            precision: Optional[float] = (len(true_retrieved) / len(result.candidates)) * 100.0
        else:
            if len(expected_cause_ids) > 0:
                precision = 0.0  # Failed to retrieve anything when causes were expected
            else:
                precision = None  # N/A: No causes expected and no candidates retrieved

        # 3. Decoy Rejection Rate: Only defined if known decoys exist
        decoys_in_candidates = decoy_ids.intersection(retrieved_ids)
        decoys_rejected_count = len(decoy_ids) - len(decoys_in_candidates)
        if len(decoy_ids) > 0:
            decoy_rejection_pct: Optional[float] = (decoys_rejected_count / len(decoy_ids)) * 100.0
        else:
            decoy_rejection_pct = None  # N/A

        # 4. Provenance Coverage: Only defined if candidates exist
        if len(result.candidates) > 0:
            prov_complete_count = sum(1 for c in result.candidates if c.is_provenance_complete)
            prov_coverage: Optional[float] = (prov_complete_count / len(result.candidates)) * 100.0
        else:
            prov_coverage = None  # N/A

        notes = ""
        if decoy_ids and len(decoys_in_candidates) > 0:
            notes = f"Decoys captured: {list(decoys_in_candidates)}"
        elif not expected_cause_ids:
            notes = "Unexplained/No-cause scenario"

        return ScenarioEvaluationRow(
            scenario_id=ground_truth.scenario.value,
            strategy=result.strategy,
            task_category=task_category,
            case_id=result.case_id,
            settlement_id=result.settlement_id,
            target_variance_inr=result.target_variance / 100.0,
            is_applicable=True,
            true_causes_expected=len(expected_cause_ids),
            true_causes_retrieved=len(true_retrieved),
            recall_pct=recall,
            candidates_retrieved=len(result.candidates),
            precision_pct=precision,
            decoys_present=len(decoy_ids),
            decoys_rejected=decoys_rejected_count,
            decoy_rejection_pct=decoy_rejection_pct,
            provenance_coverage_pct=prov_coverage,
            latency_ms=result.retrieval_latency_ms,
            notes=notes,
        )

    @staticmethod
    def aggregate_strategy_metrics(
        strategy: RetrievalStrategy, rows: List[ScenarioEvaluationRow]
    ) -> StrategyMetrics:
        strat_rows = [r for r in rows if r.strategy == strategy]
        if not strat_rows:
            return StrategyMetrics(
                strategy=strategy,
                total_cases_evaluated=0,
                applicable_cases=0,
                na_cases=0,
                true_causes_expected=0,
                true_causes_retrieved=0,
                evidence_recall_pct=None,
                total_candidates_retrieved=0,
                true_candidates_count=0,
                candidate_precision_pct=None,
                total_known_decoys=0,
                decoys_rejected=0,
                decoy_rejection_rate_pct=None,
                total_provenance_verified=0,
                provenance_coverage_pct=None,
                avg_latency_ms=0.0,
                median_latency_ms=0.0,
                max_latency_ms=0.0,
            )

        app_rows = [r for r in strat_rows if r.is_applicable]
        na_count = len(strat_rows) - len(app_rows)

        # Aggregate Recall: over applicable rows where true_causes_expected > 0
        recall_rows = [r for r in app_rows if r.true_causes_expected > 0]
        total_expected_causes = sum(r.true_causes_expected for r in recall_rows)
        total_retrieved_causes = sum(r.true_causes_retrieved for r in recall_rows)
        agg_recall = (
            (total_retrieved_causes / total_expected_causes) * 100.0
            if total_expected_causes > 0
            else None
        )

        # Aggregate Precision: over applicable rows where candidates_retrieved > 0
        prec_rows = [r for r in app_rows if r.candidates_retrieved > 0]
        total_cands = sum(r.candidates_retrieved for r in prec_rows)
        total_true_cands = sum(r.true_causes_retrieved for r in prec_rows)
        agg_prec = (
            (total_true_cands / total_cands) * 100.0
            if total_cands > 0
            else None
        )

        # Aggregate Decoy Rejection: over applicable rows where decoys_present > 0
        decoy_rows = [r for r in app_rows if r.decoys_present > 0]
        total_decoys = sum(r.decoys_present for r in decoy_rows)
        total_decoys_rej = sum(r.decoys_rejected for r in decoy_rows)
        agg_decoy_rej = (
            (total_decoys_rej / total_decoys) * 100.0
            if total_decoys > 0
            else None
        )

        # Aggregate Provenance Coverage: average over applicable rows with candidates
        prov_rows = [r for r in app_rows if r.provenance_coverage_pct is not None]
        agg_prov = (
            statistics.mean([r.provenance_coverage_pct for r in prov_rows])
            if prov_rows
            else None
        )

        latencies = [r.latency_ms for r in strat_rows]
        avg_lat = statistics.mean(latencies) if latencies else 0.0
        med_lat = statistics.median(latencies) if latencies else 0.0
        max_lat = max(latencies) if latencies else 0.0

        return StrategyMetrics(
            strategy=strategy,
            total_cases_evaluated=len(strat_rows),
            applicable_cases=len(app_rows),
            na_cases=na_count,
            true_causes_expected=total_expected_causes,
            true_causes_retrieved=total_retrieved_causes,
            evidence_recall_pct=agg_recall,
            total_candidates_retrieved=sum(r.candidates_retrieved for r in app_rows),
            true_candidates_count=total_retrieved_causes,
            candidate_precision_pct=agg_prec,
            total_known_decoys=total_decoys,
            decoys_rejected=total_decoys_rej,
            decoy_rejection_rate_pct=agg_decoy_rej,
            total_provenance_verified=sum(1 for r in app_rows if r.provenance_coverage_pct == 100.0),
            provenance_coverage_pct=agg_prov,
            avg_latency_ms=avg_lat,
            median_latency_ms=med_lat,
            max_latency_ms=max_lat,
        )
