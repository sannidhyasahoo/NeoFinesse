import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from neofinesse.ai_investigation.comparison import InvestigationComparator, PhaseComparisonSummary
from neofinesse.ai_investigation.investigator import AIEvidenceConstrainedInvestigator
from neofinesse.ai_investigation.llm_client import BaseLLMClient, MockLLMClient
from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestedDataset, IngestionPipeline
from neofinesse.models.ground_truth import CaseGroundTruth


class AIBenchmarkRunner:
    """Executes comparative evaluation between Phase 5 (Deterministic) and Phase 6 (AI Evidence-Constrained)."""

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.comparator = InvestigationComparator(llm_client=llm_client)

    def run_benchmark(
        self,
        dataset: IngestedDataset,
        ground_truth_path: str,
        export_dir: str = "experiments/phase6",
    ) -> PhaseComparisonSummary:
        # Load ground truth cases
        with open(ground_truth_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

        ground_truths = [CaseGroundTruth.model_validate(gt) for gt in gt_data]

        # Execute side-by-side comparison
        summary = self.comparator.compare_cases(dataset, ground_truths)

        # Export results to JSON and CSV
        out_dir = Path(export_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        json_path = out_dir / "results.json"
        csv_path = out_dir / "results.csv"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary.model_dump(), f, indent=2)

        fieldnames = [
            "Scenario",
            "Case ID",
            "Settlement ID",
            "Variance (INR)",
            "Expected Outcome",
            "Phase 5 Outcome",
            "Phase 6 AI Recommendation",
            "Phase 6 Verified Outcome",
            "Phase 5 Match",
            "Phase 6 Match",
            "AI Helped",
            "Verifier Corrected AI",
            "Conflicts Count",
            "Missing Evidence Count",
            "Phase 5 Latency (ms)",
            "Phase 6 Total Latency (ms)",
            "Phase 6 LLM Latency (ms)",
            "Phase 6 Verifier Latency (ms)",
        ]

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(fieldnames)
            for r in summary.comparison_rows:
                writer.writerow(
                    [
                        r.scenario_id,
                        r.case_id,
                        r.settlement_id,
                        f"{r.target_variance_inr:.2f}",
                        r.expected_outcome,
                        r.phase5_outcome,
                        r.phase6_ai_recommendation or "None",
                        r.phase6_verified_outcome,
                        "PASS" if r.phase5_match else "FAIL",
                        "PASS" if r.phase6_match else "FAIL",
                        "YES" if r.ai_helped else "NO",
                        "YES" if r.verifier_corrected_ai else "NO",
                        r.conflicts_count,
                        r.missing_evidence_count,
                        f"{r.phase5_latency_ms:.2f}",
                        f"{r.phase6_total_latency_ms:.2f}",
                        f"{r.phase6_llm_latency_ms:.2f}",
                        f"{r.phase6_verif_latency_ms:.2f}",
                    ]
                )

        return summary


def run_standalone_ai_benchmark() -> None:
    """CLI runner executing the Phase 5 vs Phase 6 comparison benchmark."""
    print("=== NeoFinesse: Phase 6 AI Investigation Benchmark ===")
    config = GeneratorConfig(seed=42)
    world = FinancialDataGenerator(config).generate()
    exporter = DataExporter(world, config)
    res = exporter.export_all()

    pipeline = IngestionPipeline(data_dir=res["data_dir"])
    dataset = pipeline.run()

    runner = AIBenchmarkRunner()
    summary = runner.run_benchmark(dataset, res["ground_truth_path"], export_dir="experiments/phase6")

    print("\n" + "=" * 80)
    print("PHASE 5 vs PHASE 6 COMPARATIVE SCORECARD")
    print("=" * 80)
    print(f"Total Scenarios Evaluated:         {summary.total_cases}")
    print(f"Phase 5 Root Cause Accuracy:       {summary.phase5_accuracy_pct:.1f}%")
    print(f"Phase 6 AI-Guarded Accuracy:       {summary.phase6_accuracy_pct:.1f}%")
    print(f"Phase 5 False Closure Rate:        {summary.phase5_false_closure_rate_pct:.1f}% ({summary.phase5_false_closures} false closures)")
    print(f"Phase 6 False Closure Rate:        {summary.phase6_false_closure_rate_pct:.1f}% ({summary.phase6_false_closures} false closures)")
    print(f"Total Conflicts Surfaced:          {summary.total_conflicts_surfaced}")
    print(f"Total Missing Evidence Surfaced:   {summary.total_missing_evidence_surfaced}")
    print(f"Verifier Corrections (Safety):     {summary.verifier_corrections_count}")
    print(f"Cases Where AI Helped:             {summary.ai_helped_count}")
    print(f"Avg Latency (Phase 5 Baseline):    {summary.avg_phase5_latency_ms:.2f} ms")
    print(f"Avg Latency (Phase 6 AI-Guarded):  {summary.avg_phase6_latency_ms:.2f} ms")
    print("=" * 80)
    print("Results exported to 'experiments/phase6/results.json' and 'experiments/phase6/results.csv'.")


if __name__ == "__main__":
    run_standalone_ai_benchmark()
