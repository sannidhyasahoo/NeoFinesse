import statistics
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.models.ground_truth import CaseGroundTruth
from neofinesse.retrieval.base import RetrievalResult, RetrievalStrategy


class StrategyMetrics(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    strategy: RetrievalStrategy
    total_cases_evaluated: int
    true_causes_expected: int
    true_causes_retrieved: int
    evidence_recall_pct: float
    total_candidates_retrieved: int
    true_candidates_count: int
    candidate_precision_pct: float
    total_known_decoys: int
    decoys_rejected: int
    decoy_rejection_rate_pct: float
    total_provenance_verified: int
    provenance_coverage_pct: float
    avg_latency_ms: float
    median_latency_ms: float
    max_latency_ms: float


class ScenarioEvaluationRow(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    scenario_id: str
    strategy: RetrievalStrategy
    case_id: str
    settlement_id: str
    target_variance_inr: float
    true_causes_expected: int
    true_causes_retrieved: int
    recall_pct: float
    candidates_retrieved: int
    precision_pct: float
    decoys_present: int
    decoys_rejected: int
    decoy_rejection_pct: float
    provenance_coverage_pct: float
    latency_ms: float
    notes: str


class RetrievalEvaluator:
    """Evaluates retrieval results against Ground Truth across all performance dimensions."""

    @staticmethod
    def evaluate_scenario(
        result: RetrievalResult, ground_truth: CaseGroundTruth
    ) -> ScenarioEvaluationRow:
        expected_cause_ids = {c.entity_id for c in ground_truth.true_causes}
        retrieved_ids = {c.entity_id for c in result.candidates}

        # Check true causes retrieved
        true_retrieved = expected_cause_ids.intersection(retrieved_ids)
        recall = (len(true_retrieved) / max(1, len(expected_cause_ids))) * 100.0 if expected_cause_ids else 100.0

        # Precision calculation
        precision = (len(true_retrieved) / max(1, len(result.candidates))) * 100.0 if result.candidates else (100.0 if not expected_cause_ids else 0.0)

        # Decoy rejection calculation
        decoy_ids = {d.entity_id for d in ground_truth.decoys}
        decoys_in_candidates = decoy_ids.intersection(retrieved_ids)
        decoys_rejected_count = len(decoy_ids) - len(decoys_in_candidates)
        decoy_rejection_pct = (decoys_rejected_count / max(1, len(decoy_ids))) * 100.0 if decoy_ids else 100.0

        # Provenance coverage
        prov_complete_count = sum(1 for c in result.candidates if c.is_provenance_complete)
        prov_coverage = (prov_complete_count / max(1, len(result.candidates))) * 100.0 if result.candidates else 100.0

        notes = ""
        if decoy_ids and len(decoys_in_candidates) > 0:
            notes = f"Decoys captured: {list(decoys_in_candidates)}"
        elif not expected_cause_ids:
            notes = "Unexplained/No-cause scenario"

        return ScenarioEvaluationRow(
            scenario_id=ground_truth.scenario.value,
            strategy=result.strategy,
            case_id=result.case_id,
            settlement_id=result.settlement_id,
            target_variance_inr=result.target_variance / 100.0,
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
                true_causes_expected=0,
                true_causes_retrieved=0,
                evidence_recall_pct=0.0,
                total_candidates_retrieved=0,
                true_candidates_count=0,
                candidate_precision_pct=0.0,
                total_known_decoys=0,
                decoys_rejected=0,
                decoy_rejection_rate_pct=0.0,
                total_provenance_verified=0,
                provenance_coverage_pct=0.0,
                avg_latency_ms=0.0,
                median_latency_ms=0.0,
                max_latency_ms=0.0,
            )

        total_expected = sum(r.true_causes_expected for r in strat_rows)
        total_retrieved = sum(r.true_causes_retrieved for r in strat_rows)
        total_cands = sum(r.candidates_retrieved for r in strat_rows)
        total_decoys = sum(r.decoys_present for r in strat_rows)
        total_decoys_rej = sum(r.decoys_rejected for r in strat_rows)

        recall = (total_retrieved / max(1, total_expected)) * 100.0 if total_expected > 0 else 100.0
        precision = (total_retrieved / max(1, total_cands)) * 100.0 if total_cands > 0 else 100.0
        decoy_rej = (total_decoys_rej / max(1, total_decoys)) * 100.0 if total_decoys > 0 else 100.0

        latencies = [r.latency_ms for r in strat_rows]
        avg_lat = statistics.mean(latencies) if latencies else 0.0
        med_lat = statistics.median(latencies) if latencies else 0.0
        max_lat = max(latencies) if latencies else 0.0

        # Provenance coverage calculation
        prov_pcts = [r.provenance_coverage_pct for r in strat_rows]
        avg_prov = statistics.mean(prov_pcts) if prov_pcts else 100.0

        return StrategyMetrics(
            strategy=strategy,
            total_cases_evaluated=len(strat_rows),
            true_causes_expected=total_expected,
            true_causes_retrieved=total_retrieved,
            evidence_recall_pct=recall,
            total_candidates_retrieved=total_cands,
            true_candidates_count=total_retrieved,
            candidate_precision_pct=precision,
            total_known_decoys=total_decoys,
            decoys_rejected=total_decoys_rej,
            decoy_rejection_rate_pct=decoy_rej,
            total_provenance_verified=sum(1 for r in strat_rows if r.provenance_coverage_pct == 100.0),
            provenance_coverage_pct=avg_prov,
            avg_latency_ms=avg_lat,
            median_latency_ms=med_lat,
            max_latency_ms=max_lat,
        )
