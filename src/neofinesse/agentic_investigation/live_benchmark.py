import csv
import json
import os
from pathlib import Path
import statistics
import time
from typing import Any, Dict, List, Optional

from neofinesse.agentic_investigation.controller import AgenticInvestigationController
from neofinesse.agentic_investigation.llm_client import GenericLLMClient
from neofinesse.agentic_investigation.models import FailureType
from neofinesse.agentic_investigation.planner import LiveAgentPlanner
from neofinesse.agentic_investigation.tools import InvestigationTools
from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestedDataset, IngestionPipeline
from neofinesse.investigation.models import InvestigationStatus
from neofinesse.retrieval.evaluator import get_scenario_task_category


class LiveAgenticBenchmarkRunner:
    """Evaluates the 23 controlled scenarios using a Live LLM Client, saving results separately to experiments/phase7/live/."""

    def __init__(self, llm_client: Optional[GenericLLMClient] = None):
        self.llm_client = llm_client or GenericLLMClient()

    def run_live_benchmark(
        self,
        dataset: IngestedDataset,
        ground_truth_path: str,
        export_dir: str = "experiments/phase7/live",
    ) -> Dict[str, Any]:
        with open(ground_truth_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

        from neofinesse.models.ground_truth import CaseGroundTruth
        from neofinesse.agentic_investigation.benchmark import AgenticBenchmarkRunner

        base_gts = [CaseGroundTruth.model_validate(gt) for gt in gt_data]
        scenario_specs = AgenticBenchmarkRunner().generate_agentic_scenario_definitions(base_gts)

        live_controller = AgenticInvestigationController(
            planner=LiveAgentPlanner(llm_client=self.llm_client),
        )

        scenario_results: List[Dict[str, Any]] = []
        n = len(scenario_specs)

        correct_count = 0
        false_closures = 0
        false_escalations = 0
        honest_exceptions = 0
        unresolvable_total = 0
        resolvable_total = 0

        llm_latencies: List[float] = []
        tool_latencies: List[float] = []
        orchestration_latencies: List[float] = []
        total_latencies: List[float] = []
        token_counts: List[int] = []

        for spec in scenario_specs:
            scen_id = spec["scenario_id"]
            case_id = spec["case_id"]
            setl_id = spec["settlement_id"]
            category = spec["category"]
            exp_outcome = spec["expected_outcome"]

            is_unresolvable = exp_outcome == "ESCALATE"
            if is_unresolvable:
                unresolvable_total += 1
            else:
                resolvable_total += 1

            target_var = spec["target_variance_paise"]

            # Execute Live Controller
            live_res = live_controller.investigate(
                case_id=case_id,
                settlement_id=setl_id,
                target_variance=target_var,
                dataset=dataset,
                scenario_id=scen_id,
            )

            is_match = live_res.final_status.value == exp_outcome
            if is_match:
                correct_count += 1
                if is_unresolvable:
                    honest_exceptions += 1

            # Failure classification
            failure_type = FailureType.NONE
            if not is_match:
                if is_unresolvable and live_res.final_status in (
                    InvestigationStatus.RESOLVED,
                    InvestigationStatus.VALID_DELAYED_CREDIT,
                ):
                    failure_type = FailureType.FALSE_CLOSURE
                    false_closures += 1
                elif not is_unresolvable and live_res.final_status == InvestigationStatus.ESCALATE:
                    failure_type = FailureType.FALSE_ESCALATION
                    false_escalations += 1
                else:
                    failure_type = FailureType.OTHER

            # Latency and token accounting
            llm_latencies.append(live_res.llm_latency_ms)
            tool_latencies.append(live_res.tool_latency_ms)
            orchestration_latencies.append(live_res.orchestration_latency_ms)
            total_latencies.append(live_res.investigation_latency_ms)
            if live_res.llm_tokens_used is not None:
                token_counts.append(live_res.llm_tokens_used)

            # Causal evidence efficiency
            req_causal = spec.get("required_causal_count", 0)
            unique_evidence_count = len(live_res.state_snapshot.get("current_evidence", {}))
            eff = min(100.0, (req_causal / max(1, unique_evidence_count)) * 100.0) if req_causal > 0 else None

            scenario_results.append(
                {
                    "scenario_id": scen_id,
                    "case_id": case_id,
                    "settlement_id": setl_id,
                    "category": category,
                    "target_variance_inr": target_var / 100.0,
                    "expected_outcome": exp_outcome,
                    "final_decision": live_res.final_status.value,
                    "is_correct": "PASS" if is_match else "FAIL",
                    "failure_type": failure_type.value,
                    "termination_reason": live_res.termination_reason,
                    "rounds_executed": live_res.total_rounds,
                    "tool_calls_executed": live_res.total_tool_calls,
                    "evidence_efficiency_pct": eff,
                    "model": live_res.llm_model,
                    "provider": live_res.llm_provider,
                    "tokens_used": live_res.llm_tokens_used,
                    "local_orchestration_latency_ms": live_res.orchestration_latency_ms,
                    "llm_latency_ms": live_res.llm_latency_ms,
                    "tool_latency_ms": live_res.tool_latency_ms,
                    "end_to_end_latency_ms": live_res.investigation_latency_ms,
                }
            )

        # Build Summary Report
        summary = {
            "total_scenarios_evaluated": n,
            "provider": self.llm_client.provider_name,
            "model": self.llm_client.model_name,
            "is_live_remote": self.llm_client.is_live_configured,
            "correct_terminal_decision_rate_pct": (correct_count / n) * 100.0,
            "false_closure_rate_pct": (false_closures / unresolvable_total * 100.0) if unresolvable_total else None,
            "false_escalation_rate_pct": (false_escalations / resolvable_total * 100.0) if resolvable_total else None,
            "honest_exception_rate_pct": (honest_exceptions / unresolvable_total * 100.0) if unresolvable_total else None,
            "avg_rounds": statistics.mean([r["rounds_executed"] for r in scenario_results]),
            "avg_tool_calls": statistics.mean([r["tool_calls_executed"] for r in scenario_results]),
            "avg_orchestration_latency_ms": statistics.mean(orchestration_latencies) if orchestration_latencies else 0.0,
            "avg_llm_latency_ms": statistics.mean(llm_latencies) if llm_latencies else 0.0,
            "avg_tool_latency_ms": statistics.mean(tool_latencies) if tool_latencies else 0.0,
            "avg_end_to_end_latency_ms": statistics.mean(total_latencies) if total_latencies else 0.0,
            "avg_tokens_used": statistics.mean(token_counts) if token_counts else None,
            "scenario_results": scenario_results,
        }

        # Export strictly to experiments/phase7/live/
        out_dir = Path(export_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        with open(out_dir / "results.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        with open(out_dir / "results.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Scenario",
                    "Category",
                    "Expected",
                    "Decision",
                    "Result",
                    "Failure Type",
                    "Termination Reason",
                    "Rounds",
                    "Tool Calls",
                    "Model",
                    "Provider",
                    "Tokens",
                    "Orchestration Latency (ms)",
                    "LLM Latency (ms)",
                    "Tool Latency (ms)",
                    "End-to-End Latency (ms)",
                ]
            )
            for r in scenario_results:
                writer.writerow(
                    [
                        r["scenario_id"],
                        r["category"],
                        r["expected_outcome"],
                        r["final_decision"],
                        r["is_correct"],
                        r["failure_type"],
                        r["termination_reason"],
                        r["rounds_executed"],
                        r["tool_calls_executed"],
                        r["model"],
                        r["provider"],
                        r["tokens_used"] if r["tokens_used"] is not None else "N/A",
                        f"{r['local_orchestration_latency_ms']:.2f}",
                        f"{r['llm_latency_ms']:.2f}",
                        f"{r['tool_latency_ms']:.2f}",
                        f"{r['end_to_end_latency_ms']:.2f}",
                    ]
                )

        return summary


def run_standalone_live_benchmark() -> None:
    """CLI runner executing the Phase 7.2 Live AI benchmark."""
    config = GeneratorConfig(seed=42)
    world = FinancialDataGenerator(config).generate()
    exporter = DataExporter(world, config)
    res = exporter.export_all()

    pipeline = IngestionPipeline(data_dir=res["data_dir"])
    dataset = pipeline.run()

    runner = LiveAgenticBenchmarkRunner()
    summary = runner.run_live_benchmark(dataset, res["ground_truth_path"])

    print("\n" + "=" * 80)
    print(f"NEOFINESSE PHASE 7.2 LIVE AI BENCHMARK RESULTS")
    print(f"Provider: {summary['provider']} | Model: {summary['model']} | Live Remote: {summary['is_live_remote']}")
    print("=" * 80)
    print(f"Correct Terminal Decision Rate:   {summary['correct_terminal_decision_rate_pct']:.1f}% ({round(summary['correct_terminal_decision_rate_pct'] * 23 / 100)} / 23)")
    fc_str = f"{summary['false_closure_rate_pct']:.1f}%" if summary['false_closure_rate_pct'] is not None else "N/A"
    fe_str = f"{summary['false_escalation_rate_pct']:.1f}%" if summary['false_escalation_rate_pct'] is not None else "N/A"
    he_str = f"{summary['honest_exception_rate_pct']:.1f}%" if summary['honest_exception_rate_pct'] is not None else "N/A"
    print(f"False Closure Rate:               {fc_str}")
    print(f"False Escalation Rate:            {fe_str}")
    print(f"Honest Exception Rate:            {he_str}")
    print(f"Average Investigation Rounds:     {summary['avg_rounds']:.1f}")
    print(f"Average Tool Calls per Case:      {summary['avg_tool_calls']:.1f}")
    print("\nLatency & Cost Accounting Breakdown:")
    print(f" - Local Orchestration Time:      {summary['avg_orchestration_latency_ms']:.2f} ms")
    print(f" - LLM Response Time:             {summary['avg_llm_latency_ms']:.2f} ms")
    print(f" - Tool Execution Time:           {summary['avg_tool_latency_ms']:.2f} ms")
    print(f" - End-to-End Total Time:         {summary['avg_end_to_end_latency_ms']:.2f} ms")
    if summary['avg_tokens_used'] is not None:
        print(f" - Average Tokens Consumed:       {summary['avg_tokens_used']:.0f}")
    print("=" * 80)
    print("Results exported to 'experiments/phase7/live/results.json' and 'experiments/phase7/live/results.csv'.")


if __name__ == "__main__":
    run_standalone_live_benchmark()
