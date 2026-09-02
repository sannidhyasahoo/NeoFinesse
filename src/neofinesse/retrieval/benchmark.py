import csv
import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.models.ground_truth import CaseGroundTruth
from neofinesse.retrieval.attribute import AttributeRetrievalStrategy
from neofinesse.retrieval.base import (
    BaseRetrievalStrategy,
    InvestigationTaskCategory,
    RetrievalResult,
    RetrievalStrategy,
)
from neofinesse.retrieval.direct_id import DirectIdRetrievalStrategy
from neofinesse.retrieval.evaluator import (
    RetrievalEvaluator,
    ScenarioEvaluationRow,
    StrategyMetrics,
    get_scenario_task_category,
)
from neofinesse.retrieval.provenance import TypedProvenanceRetrievalStrategy
from neofinesse.retrieval.relationship import RelationshipAwareRetrievalStrategy
from neofinesse.retrieval.temporal import TemporalRelationshipRetrievalStrategy
from neofinesse.retrieval.upi_event import UPIEventRetrievalStrategy


class BenchmarkExperimentReport(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    total_experiments_run: int
    strategies_evaluated: List[RetrievalStrategy]
    strategy_metrics: Dict[str, StrategyMetrics]
    scenario_matrix: List[ScenarioEvaluationRow]


class RetrievalBenchmarkRunner:
    """Orchestrates Phase 4 multi-strategy retrieval experiments against the 10 failure injection scenarios."""

    def __init__(self):
        self.strategies: Dict[RetrievalStrategy, BaseRetrievalStrategy] = {
            RetrievalStrategy.DIRECT_ID: DirectIdRetrievalStrategy(),
            RetrievalStrategy.ATTRIBUTE: AttributeRetrievalStrategy(),
            RetrievalStrategy.RELATIONSHIP: RelationshipAwareRetrievalStrategy(),
            RetrievalStrategy.TYPED_PROVENANCE: TypedProvenanceRetrievalStrategy(),
            RetrievalStrategy.TEMPORAL_RELATIONSHIP: TemporalRelationshipRetrievalStrategy(),
            RetrievalStrategy.UPI_EVENT: UPIEventRetrievalStrategy(),
        }

    def run_all_experiments(
        self, dataset: IngestedDataset, ground_truth_path: str, export_dir: Optional[str] = None
    ) -> BenchmarkExperimentReport:
        gt_file = Path(ground_truth_path)
        if not gt_file.exists():
            raise FileNotFoundError(f"Ground truth file not found: {gt_file}")

        with open(gt_file, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

        ground_truths = [CaseGroundTruth.model_validate(item) for item in gt_data]

        all_rows: List[ScenarioEvaluationRow] = []

        # Run each strategy against each ground truth scenario
        for gt in ground_truths:
            setl_id = gt.settlement_id
            variance = gt.expected_variance
            task_category = get_scenario_task_category(gt.scenario.value)

            for strat_enum, strat_impl in self.strategies.items():
                res = strat_impl.retrieve(
                    case_id=gt.case_id,
                    settlement_id=setl_id,
                    target_variance=variance,
                    dataset=dataset,
                    task_category=task_category,
                )
                eval_row = RetrievalEvaluator.evaluate_scenario(res, gt)
                all_rows.append(eval_row)

        # Aggregate metrics per strategy
        strat_metrics: Dict[str, StrategyMetrics] = {}
        for strat_enum in self.strategies.keys():
            strat_metrics[strat_enum.value] = RetrievalEvaluator.aggregate_strategy_metrics(
                strat_enum, all_rows
            )

        report = BenchmarkExperimentReport(
            total_experiments_run=len(all_rows),
            strategies_evaluated=list(self.strategies.keys()),
            strategy_metrics=strat_metrics,
            scenario_matrix=all_rows,
        )

        # Optionally export results to JSON and CSV
        if export_dir:
            out_path = Path(export_dir)
            out_path.mkdir(parents=True, exist_ok=True)

            # 1. Export JSON
            json_file = out_path / "results.json"
            with open(json_file, "w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))

            # 2. Export CSV matrix
            csv_file = out_path / "results.csv"
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "Scenario",
                        "Strategy",
                        "Task Category",
                        "Case ID",
                        "Settlement ID",
                        "Variance (INR)",
                        "Applicable",
                        "True Causes Expected",
                        "True Causes Retrieved",
                        "Recall (%)",
                        "Candidates Retrieved",
                        "Precision (%)",
                        "Decoys Present",
                        "Decoys Rejected",
                        "Decoy Rejection (%)",
                        "Provenance Coverage (%)",
                        "Latency (ms)",
                        "Notes",
                    ]
                )
                for r in all_rows:
                    recall_str = f"{r.recall_pct:.1f}%" if r.recall_pct is not None else "N/A"
                    prec_str = f"{r.precision_pct:.1f}%" if r.precision_pct is not None else "N/A"
                    decoy_rej_str = f"{r.decoy_rejection_pct:.1f}%" if r.decoy_rejection_pct is not None else "N/A"
                    prov_cov_str = f"{r.provenance_coverage_pct:.1f}%" if r.provenance_coverage_pct is not None else "N/A"

                    writer.writerow(
                        [
                            r.scenario_id,
                            r.strategy.value,
                            r.task_category.value,
                            r.case_id,
                            r.settlement_id,
                            f"{r.target_variance_inr:.2f}",
                            "YES" if r.is_applicable else "NO (N/A)",
                            r.true_causes_expected if r.is_applicable else "N/A",
                            r.true_causes_retrieved if r.is_applicable else "N/A",
                            recall_str,
                            r.candidates_retrieved,
                            prec_str,
                            r.decoys_present if r.is_applicable else "N/A",
                            r.decoys_rejected if r.is_applicable else "N/A",
                            decoy_rej_str,
                            prov_cov_str,
                            f"{r.latency_ms:.2f}",
                            r.notes,
                        ]
                    )

        return report


def main() -> None:
    from neofinesse.generator.config import GeneratorConfig
    from neofinesse.generator.exporter import DataExporter
    from neofinesse.generator.synthetic import FinancialDataGenerator
    from neofinesse.ingestion.pipeline import IngestionPipeline

    print("=== NeoFinesse: Phase 4 Retrieval Benchmark ===")
    config = GeneratorConfig(seed=42)
    world = FinancialDataGenerator(config).generate()
    exporter = DataExporter(world, config)
    res = exporter.export_all()

    pipeline = IngestionPipeline(data_dir=res["data_dir"])
    dataset = pipeline.run()

    runner = RetrievalBenchmarkRunner()
    report = runner.run_all_experiments(
        dataset=dataset,
        ground_truth_path=res["ground_truth_path"],
        export_dir="experiments/phase4",
    )

    print(f"\nTotal Experiments Run: {report.total_experiments_run}")
    print("=" * 110)
    print(f"{'Strategy':<22} | {'Applicable':<10} | {'Recall (%)':<12} | {'Precision (%)':<14} | {'Decoy Rej (%)':<14} | {'Prov Cov (%)':<12} | {'Latency':<8}")
    print("-" * 110)
    for strat, metrics in report.strategy_metrics.items():
        rec = f"{metrics.evidence_recall_pct:.1f}%" if metrics.evidence_recall_pct is not None else "N/A"
        prec = f"{metrics.candidate_precision_pct:.1f}%" if metrics.candidate_precision_pct is not None else "N/A"
        decoy = f"{metrics.decoy_rejection_rate_pct:.1f}%" if metrics.decoy_rejection_rate_pct is not None else "N/A"
        prov = f"{metrics.provenance_coverage_pct:.1f}%" if metrics.provenance_coverage_pct is not None else "N/A"
        app_str = f"{metrics.applicable_cases}/{metrics.total_cases_evaluated}"
        print(f"{strat:<22} | {app_str:<10} | {rec:<12} | {prec:<14} | {decoy:<14} | {prov:<12} | {metrics.avg_latency_ms:.2f}ms")
    print("=" * 110)
    print("Exported results to 'experiments/phase4/results.json' and 'experiments/phase4/results.csv'.")


if __name__ == "__main__":
    main()
