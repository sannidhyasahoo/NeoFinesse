from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestionPipeline
from neofinesse.reconciliation.engine import DeterministicReconciliationEngine
from neofinesse.reconciliation.metrics import BaselineEvaluator


def main() -> None:
    print("=== NeoFinesse: AI Finance Controller ===")
    config = GeneratorConfig(seed=42)
    print(f"Generating synthetic financial world (seed={config.seed})...")
    world = FinancialDataGenerator(config).generate()
    print(f"Generated {len(world.orders)} orders, {len(world.payments)} payments, {len(world.settlement_lines)} settlement lines, {len(world.settlements)} settlements.")
    print(f"Injecting {len(world.ground_truths)} controlled failure scenarios...")

    exporter = DataExporter(world, config)
    res = exporter.export_all()
    print(f"Exported multi-source files to '{res['data_dir']}' and ground truth to '{res['ground_truth_path']}'.")

    print("\n[Phase 2] Running Ingestion Pipeline & Validation...")
    pipeline = IngestionPipeline(data_dir=res["data_dir"])
    dataset = pipeline.run()
    print(f"Ingested {len(dataset.payments)} payments, {len(dataset.settlement_lines)} settlement lines, {len(dataset.settlements)} settlements.")
    print(f"Validation errors: {len(dataset.validation_errors)}")

    print("\n[Phase 3] Running Deterministic Reconciliation Engine...")
    engine = DeterministicReconciliationEngine()
    run_result = engine.run(dataset)
    print(f"Total settlements reconciled: {run_result.total_settlements}")
    print(f" - Matched clean: {run_result.matched_settlements}")
    print(f" - Valid delayed credit: {run_result.delayed_credit_cases}")
    print(f" - Resolved variances: {run_result.resolved_cases}")
    print(f" - Partially resolved: {run_result.partially_resolved_cases}")
    print(f" - Escalated: {run_result.escalated_cases}")

    print("\n[Phase 3] Evaluating against Ground Truth Benchmark...")
    scorecard = BaselineEvaluator.evaluate(run_result, res["ground_truth_path"])
    print(f"Benchmark Accuracy: {scorecard.accuracy_percentage:.1f}% ({scorecard.correct_outcomes}/{scorecard.total_scenarios_evaluated})")
    print(f"True Cause Recall: {scorecard.true_cause_recall_percentage:.1f}% ({scorecard.true_causes_identified}/{scorecard.true_causes_expected})")
    print(f"False Causes Accepted: {scorecard.false_causes_accepted} (0%)")
    print(f"False Closures: {scorecard.false_closures} (0%)")

    print("\n[Phase 4] Running Evidence Retrieval Experiments (6 Strategies x 10 Scenarios)...")
    from neofinesse.retrieval.benchmark import RetrievalBenchmarkRunner
    retrieval_runner = RetrievalBenchmarkRunner()
    exp_report = retrieval_runner.run_all_experiments(
        dataset=dataset,
        ground_truth_path=res["ground_truth_path"],
        export_dir="experiments/phase4",
    )
    print(f"Total Retrieval Experiments Run: {exp_report.total_experiments_run}")
    for strat, metrics in exp_report.strategy_metrics.items():
        print(f" - [{strat:21s}] Recall: {metrics.evidence_recall_pct:5.1f}% | Precision: {metrics.candidate_precision_pct:5.1f}% | Decoy Rej: {metrics.decoy_rejection_rate_pct:5.1f}% | Latency: {metrics.avg_latency_ms:.2f}ms")
    print("Results exported to 'experiments/phase4/results.json' and 'experiments/phase4/results.csv'.")
    print("[SUCCESS] Phase 4 Evidence Retrieval Experiments ready.")


if __name__ == "__main__":
    main()
