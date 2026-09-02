import csv
import json
from pathlib import Path
import statistics
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.investigation.investigator import VarianceInvestigator
from neofinesse.investigation.models import InvestigationResult, InvestigationStatus
from neofinesse.models.ground_truth import CaseGroundTruth, ExpectedOutcome


class InvestigationBenchmarkScorecard(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    total_scenarios_evaluated: int
    correct_outcomes: int
    root_cause_accuracy_pct: float
    false_closures: int
    false_closure_rate_pct: float
    partial_attributions_correct: int
    partial_attribution_accuracy_pct: float
    honest_exceptions_correct: int
    honest_exception_rate_pct: float
    avg_latency_ms: float
    median_latency_ms: float
    max_latency_ms: float
    scenario_results: List[Dict[str, Any]] = Field(default_factory=list)


class InvestigationBenchmarkRunner:
    """Orchestrates Phase 5 investigation benchmark across all 10 ground truth scenarios."""

    def __init__(self):
        self.investigator = VarianceInvestigator()

    def run_benchmark(
        self, dataset: IngestedDataset, ground_truth_path: str, export_dir: Optional[str] = None
    ) -> InvestigationBenchmarkScorecard:
        gt_file = Path(ground_truth_path)
        if not gt_file.exists():
            raise FileNotFoundError(f"Ground truth file not found: {gt_file}")

        with open(gt_file, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

        ground_truths = [CaseGroundTruth.model_validate(item) for item in gt_data]

        scenario_rows: List[Dict[str, Any]] = []
        latencies: List[float] = []

        correct_outcomes = 0
        false_closures = 0
        partial_correct = 0
        partial_total = 0
        honest_exceptions_correct = 0
        honest_exceptions_total = 0

        for gt in ground_truths:
            target_var = (
                -(abs(gt.explained_amount) + abs(gt.unexplained_amount))
                if gt.expected_outcome == ExpectedOutcome.PARTIALLY_RESOLVED
                else gt.expected_variance
            )

            inv_res = self.investigator.investigate(
                case_id=gt.case_id,
                settlement_id=gt.settlement_id,
                target_variance=target_var,
                dataset=dataset,
                scenario_id=gt.scenario.value,
            )

            latencies.append(inv_res.investigation_latency_ms)

            # Map status
            status_val = inv_res.final_status.value
            expected_val = gt.expected_outcome.value

            is_correct = False
            if gt.expected_outcome == ExpectedOutcome.RESOLVED and inv_res.final_status == InvestigationStatus.RESOLVED:
                is_correct = True
            elif gt.expected_outcome == ExpectedOutcome.PARTIALLY_RESOLVED and inv_res.final_status == InvestigationStatus.PARTIALLY_RESOLVED:
                is_correct = True
            elif gt.expected_outcome == ExpectedOutcome.VALID_DELAYED_CREDIT and inv_res.final_status == InvestigationStatus.VALID_DELAYED_CREDIT:
                is_correct = True
            elif gt.expected_outcome == ExpectedOutcome.ESCALATE and inv_res.final_status == InvestigationStatus.ESCALATE:
                is_correct = True

            if is_correct:
                correct_outcomes += 1

            # Check false closure: expected ESCALATE but got RESOLVED
            if gt.expected_outcome == ExpectedOutcome.ESCALATE and inv_res.final_status == InvestigationStatus.RESOLVED:
                false_closures += 1

            # Check partial attribution accuracy
            if gt.expected_outcome == ExpectedOutcome.PARTIALLY_RESOLVED:
                partial_total += 1
                if inv_res.final_status == InvestigationStatus.PARTIALLY_RESOLVED and abs(inv_res.explained_amount) == abs(gt.explained_amount):
                    partial_correct += 1

            # Check honest exceptions
            if gt.expected_outcome == ExpectedOutcome.ESCALATE:
                honest_exceptions_total += 1
                if inv_res.final_status == InvestigationStatus.ESCALATE:
                    honest_exceptions_correct += 1

            winning_id = inv_res.winning_hypothesis.hypothesis_id if inv_res.winning_hypothesis else "None"
            ev_level = inv_res.winning_hypothesis.evidence_level.value if inv_res.winning_hypothesis else "None"

            scenario_rows.append(
                {
                    "scenario_id": gt.scenario.value,
                    "case_id": gt.case_id,
                    "settlement_id": gt.settlement_id,
                    "target_variance_inr": gt.expected_variance / 100.0,
                    "expected_outcome": expected_val,
                    "observed_outcome": status_val,
                    "is_correct": is_correct,
                    "winning_hypothesis": winning_id,
                    "evidence_level": ev_level,
                    "explained_inr": inv_res.explained_amount / 100.0,
                    "unexplained_inr": inv_res.unexplained_amount / 100.0,
                    "hypotheses_evaluated": len(inv_res.hypotheses),
                    "hypotheses_rejected": len(inv_res.rejected_hypotheses),
                    "latency_ms": inv_res.investigation_latency_ms,
                }
            )

        total_scenarios = len(ground_truths)
        root_cause_acc = (correct_outcomes / total_scenarios) * 100.0 if total_scenarios > 0 else 0.0
        false_closure_rate = (false_closures / total_scenarios) * 100.0 if total_scenarios > 0 else 0.0
        partial_acc = (partial_correct / partial_total) * 100.0 if partial_total > 0 else 100.0
        honest_rate = (honest_exceptions_correct / honest_exceptions_total) * 100.0 if honest_exceptions_total > 0 else 100.0

        avg_lat = statistics.mean(latencies) if latencies else 0.0
        med_lat = statistics.median(latencies) if latencies else 0.0
        max_lat = max(latencies) if latencies else 0.0

        scorecard = InvestigationBenchmarkScorecard(
            total_scenarios_evaluated=total_scenarios,
            correct_outcomes=correct_outcomes,
            root_cause_accuracy_pct=root_cause_acc,
            false_closures=false_closures,
            false_closure_rate_pct=false_closure_rate,
            partial_attributions_correct=partial_correct,
            partial_attribution_accuracy_pct=partial_acc,
            honest_exceptions_correct=honest_exceptions_correct,
            honest_exception_rate_pct=honest_rate,
            avg_latency_ms=avg_lat,
            median_latency_ms=med_lat,
            max_latency_ms=max_lat,
            scenario_results=scenario_rows,
        )

        if export_dir:
            out_path = Path(export_dir)
            out_path.mkdir(parents=True, exist_ok=True)

            # Export JSON
            json_file = out_path / "results.json"
            with open(json_file, "w", encoding="utf-8") as f:
                f.write(scorecard.model_dump_json(indent=2))

            # Export CSV
            csv_file = out_path / "results.csv"
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "Scenario",
                        "Case ID",
                        "Settlement ID",
                        "Variance (INR)",
                        "Expected Outcome",
                        "Observed Outcome",
                        "Outcome Match",
                        "Winning Hypothesis",
                        "Evidence Level",
                        "Explained (INR)",
                        "Unexplained (INR)",
                        "Hypotheses Evaluated",
                        "Hypotheses Rejected",
                        "Latency (ms)",
                    ]
                )
                for r in scenario_rows:
                    writer.writerow(
                        [
                            r["scenario_id"],
                            r["case_id"],
                            r["settlement_id"],
                            f"{r['target_variance_inr']:.2f}",
                            r["expected_outcome"],
                            r["observed_outcome"],
                            "PASS" if r["is_correct"] else "FAIL",
                            r["winning_hypothesis"],
                            r["evidence_level"],
                            f"{r['explained_inr']:.2f}",
                            f"{r['unexplained_inr']:.2f}",
                            r["hypotheses_evaluated"],
                            r["hypotheses_rejected"],
                            f"{r['latency_ms']:.2f}",
                        ]
                    )

        return scorecard


def main() -> None:
    from neofinesse.generator.config import GeneratorConfig
    from neofinesse.generator.exporter import DataExporter
    from neofinesse.generator.synthetic import FinancialDataGenerator
    from neofinesse.ingestion.pipeline import IngestionPipeline

    print("=== NeoFinesse: Phase 5 Investigation Benchmark ===")
    config = GeneratorConfig(seed=42)
    world = FinancialDataGenerator(config).generate()
    exporter = DataExporter(world, config)
    res = exporter.export_all()

    pipeline = IngestionPipeline(data_dir=res["data_dir"])
    dataset = pipeline.run()

    runner = InvestigationBenchmarkRunner()
    scorecard = runner.run_benchmark(
        dataset=dataset,
        ground_truth_path=res["ground_truth_path"],
        export_dir="experiments/phase5",
    )

    print("\n" + "=" * 80)
    print("PHASE 5 INVESTIGATION SCORECARD")
    print("=" * 80)
    print(f"Total Scenarios Evaluated:         {scorecard.total_scenarios_evaluated}")
    print(f"Correct Outcomes:                 {scorecard.correct_outcomes} / {scorecard.total_scenarios_evaluated}")
    print(f"Root Cause Accuracy:              {scorecard.root_cause_accuracy_pct:.1f}%")
    print(f"False Closure Rate:               {scorecard.false_closure_rate_pct:.1f}% ({scorecard.false_closures} false closures)")
    print(f"Partial Attribution Accuracy:     {scorecard.partial_attribution_accuracy_pct:.1f}%")
    print(f"Honest Exception Rate:            {scorecard.honest_exception_rate_pct:.1f}%")
    print(f"Average Investigation Latency:    {scorecard.avg_latency_ms:.2f} ms")
    print(f"Median Investigation Latency:     {scorecard.median_latency_ms:.2f} ms")
    print(f"Max Investigation Latency:        {scorecard.max_latency_ms:.2f} ms")
    print("=" * 80)
    print("Results exported to 'experiments/phase5/results.json' and 'experiments/phase5/results.csv'.")


if __name__ == "__main__":
    main()
