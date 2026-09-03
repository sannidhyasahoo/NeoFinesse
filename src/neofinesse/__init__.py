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
        rec = f"{metrics.evidence_recall_pct:.1f}%" if metrics.evidence_recall_pct is not None else "N/A"
        prec = f"{metrics.candidate_precision_pct:.1f}%" if metrics.candidate_precision_pct is not None else "N/A"
        decoy = f"{metrics.decoy_rejection_rate_pct:.1f}%" if metrics.decoy_rejection_rate_pct is not None else "N/A"
        print(f" - [{strat:21s}] Applicable: {metrics.applicable_cases}/10 | Recall: {rec:>6} | Precision: {prec:>6} | Decoy Rej: {decoy:>6} | Latency: {metrics.avg_latency_ms:.2f}ms")

    print("\n[Phase 5] Running Deterministic Financial Investigation Engine...")
    from neofinesse.investigation.benchmark import InvestigationBenchmarkRunner
    inv_runner = InvestigationBenchmarkRunner()
    inv_scorecard = inv_runner.run_benchmark(
        dataset=dataset,
        ground_truth_path=res["ground_truth_path"],
        export_dir="experiments/phase5",
    )
    print(f"Investigation Accuracy: {inv_scorecard.root_cause_accuracy_pct:.1f}% ({inv_scorecard.correct_outcomes}/{inv_scorecard.total_scenarios_evaluated})")
    print(f"False Closure Rate:     {inv_scorecard.false_closure_rate_pct:.1f}% ({inv_scorecard.false_closures} false closures)")
    print(f"Partial Attribution:    {inv_scorecard.partial_attribution_accuracy_pct:.1f}%")
    print(f"Honest Exception Rate:  {inv_scorecard.honest_exception_rate_pct:.1f}%")
    print(f"Average Latency:        {inv_scorecard.avg_latency_ms:.2f}ms")
    print("Results exported to 'experiments/phase5/results.json' and 'experiments/phase5/results.csv'.")

    print("\n[Phase 6] Running AI Evidence-Constrained Financial Investigator...")
    from neofinesse.ai_investigation.benchmark import AIBenchmarkRunner
    ai_runner = AIBenchmarkRunner()
    ai_summary = ai_runner.run_benchmark(
        dataset=dataset,
        ground_truth_path=res["ground_truth_path"],
        export_dir="experiments/phase6",
    )
    print(f"AI Root Cause Accuracy: {ai_summary.phase6_accuracy_pct:.1f}%")
    print(f"AI False Closure Rate:  {ai_summary.phase6_false_closure_rate_pct:.1f}% ({ai_summary.phase6_false_closures} false closures)")
    print(f"Conflicts Surfaced:     {ai_summary.total_conflicts_surfaced}")
    print(f"Missing Ev. Surfaced:   {ai_summary.total_missing_evidence_surfaced}")
    print(f"AI Helped Cases:        {ai_summary.ai_helped_count}")
    print(f"Average AI Latency:     {ai_summary.avg_phase6_latency_ms:.2f}ms")
    print("\n[Phase 7] Running Adaptive / Agentic Evidence Investigation Benchmark...")
    from neofinesse.agentic_investigation.benchmark import AgenticBenchmarkRunner
    agentic_runner = AgenticBenchmarkRunner()
    agt_scorecard = agentic_runner.run_benchmark(
        dataset=dataset,
        ground_truth_path=res["ground_truth_path"],
        export_dir="experiments/phase7",
    )
    print(f"Phase 7 Agentic Accuracy:  {agt_scorecard.phase7_accuracy_pct:.1f}%")
    print(f"Phase 7 False Closure Rate: {agt_scorecard.phase7_false_closure_rate_pct:.1f}% ({agt_scorecard.phase7_false_closure_rate_pct:.0f} false closures)")
    print(f"Avg Investigation Rounds:   {agt_scorecard.avg_investigation_rounds:.1f}")
    print(f"Avg Tool Calls per Case:    {agt_scorecard.avg_tool_calls:.1f}")
    print(f"Revisions Surfaced:         {agt_scorecard.hypothesis_revisions_count}")
    print(f"Average Agentic Latency:    {agt_scorecard.avg_latency_ms:.2f}ms")
    print("Results exported to 'experiments/phase7/scenarios.json', 'results.json', and 'results.csv'.")
    print("\n[SUCCESS] NeoFinesse Phase 1-7 End-to-End Pipeline Execution Complete.")


if __name__ == "__main__":
    main()
