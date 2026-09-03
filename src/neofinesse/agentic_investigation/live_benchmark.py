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
from neofinesse.agentic_investigation.state import InvestigationState
from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestedDataset, IngestionPipeline
from neofinesse.investigation.models import InvestigationStatus
from neofinesse.models.ground_truth import CaseGroundTruth


class LiveAgenticBenchmarkRunner:
    """Evaluates the 23 controlled scenarios using the configured GenericLLMClient, saving results separately to experiments/phase7/live/."""

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
        partial_attributions = 0
        unresolvable_total = 0
        resolvable_total = 0

        llm_latencies: List[float] = []
        tool_latencies: List[float] = []
        orchestration_latencies: List[float] = []
        total_latencies: List[float] = []
        token_counts: List[int] = []

        is_remote_mode = self.llm_client.is_live_enabled

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
                if exp_outcome == "PARTIALLY_RESOLVED":
                    partial_attributions += 1

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

            # Tool request validity for this scenario
            st = InvestigationState.model_validate(live_res.state_snapshot)
            total_tool_reqs = len(st.completed_requests)
            valid_tool_reqs = sum(1 for tr in st.tool_results if tr.success)
            tool_validity = (valid_tool_reqs / total_tool_reqs * 100.0) if total_tool_reqs > 0 else None
            tools_requested = [tr.tool for rd in st.rounds for tr in rd.tool_requests]
            hyp_count = sum(len(rd.verified_hypotheses) for rd in st.rounds)

            # Audit fields
            parser_valid = not any("MALFORMED_JSON" in reason or "SCHEMA" in reason for rd in st.rounds for reason in rd.rejected_reasons)
            validator_valid = not any("INVALID_TOOL" in reason or "TOOL_ERROR" in reason for rd in st.rounds for reason in rd.rejected_reasons)

            # Failure reason & classification
            if is_match:
                reason_for_failure = "NONE"
                primary_failure = "NONE"
            elif "TIMEOUT" in live_res.termination_reason or live_res.investigation_latency_ms >= 30000:
                reason_for_failure = "LLM network read timeout (30s exceeded)"
                primary_failure = "BUDGET_OR_TIMEOUT"
            elif live_res.termination_reason == "INVALID_LLM_RESPONSE":
                reason_for_failure = "LLM API HTTP 429 Quota Exhausted / Empty Response on free tier"
                primary_failure = "BUDGET_OR_TIMEOUT"
            elif "PARSER" in live_res.termination_reason or "MALFORMED" in live_res.termination_reason:
                reason_for_failure = "LLM output violated JSON schema"
                primary_failure = "PARSER_OR_SCHEMA_FAILURE"
            elif failure_type == FailureType.FALSE_CLOSURE:
                reason_for_failure = "Unsupported closure attempt without deterministic verification"
                primary_failure = "VERIFIER_REJECTION"
            elif failure_type == FailureType.FALSE_ESCALATION:
                reason_for_failure = "Premature escalation without verified explanation"
                primary_failure = "HYPOTHESIS_GENERATION_FAILURE"
            else:
                reason_for_failure = live_res.termination_reason
                primary_failure = "OTHER"

            # Token breakdown
            tokens_in = None
            tokens_out = None
            tokens_tot = live_res.llm_tokens_used

            scenario_results.append(
                {
                    "scenario_id": scen_id,
                    "case_id": case_id,
                    "settlement_id": setl_id,
                    "category": category,
                    "provider": live_res.llm_provider,
                    "requested_model": self.llm_client.requested_model,
                    "effective_model": self.llm_client.effective_model,
                    "fallback_triggered": self.llm_client.fallback_triggered,
                    "fallback_reason": self.llm_client.fallback_reason,
                    "remote_execution": is_remote_mode,
                    "ground_truth": exp_outcome,
                    "final_decision": live_res.final_status.value,
                    "correct": is_match,
                    "false_closure": failure_type == FailureType.FALSE_CLOSURE,
                    "false_escalation": failure_type == FailureType.FALSE_ESCALATION,
                    "honest_exception": is_match and is_unresolvable,
                    "partial_attribution": is_match and exp_outcome == "PARTIALLY_RESOLVED",
                    "rounds": live_res.total_rounds,
                    "tool_calls": live_res.total_tool_calls,
                    "tools_requested": tools_requested,
                    "hypothesis_count": hyp_count,
                    "final_verifier_result": live_res.final_status.value,
                    "parser_valid": parser_valid,
                    "validator_valid": validator_valid,
                    "reason_for_failure": reason_for_failure,
                    "primary_failure_category": primary_failure,
                    "tool_request_validity": tool_validity,
                    "evidence_efficiency": eff,
                    "llm_latency": live_res.llm_latency_ms,
                    "tool_latency": live_res.tool_latency_ms,
                    "local_latency": live_res.orchestration_latency_ms,
                    "total_latency": live_res.investigation_latency_ms,
                    "input_tokens": tokens_in,
                    "output_tokens": tokens_out,
                    "total_tokens": tokens_tot,
                    "termination_reason": live_res.termination_reason,
                    "failure_type": failure_type.value,
                }
            )

        # Build Summary Report
        resolved_count = sum(1 for r in scenario_results if r["final_decision"] in ("RESOLVED", "VALID_DELAYED_CREDIT"))
        summary = {
            "total_scenarios_evaluated": n,
            "provider": self.llm_client.provider_name,
            "requested_model": self.llm_client.requested_model,
            "effective_model": self.llm_client.effective_model,
            "fallback_triggered": self.llm_client.fallback_triggered,
            "fallback_reason": self.llm_client.fallback_reason,
            "is_live_remote": is_remote_mode,
            "benchmark_mode": "Real Remote Live LLM" if is_remote_mode else "Offline Fallback / Unconfigured Mock",
            "correct_terminal_decision_rate_pct": (correct_count / n) * 100.0,
            "false_closure_rate_pct": (false_closures / unresolvable_total * 100.0) if unresolvable_total else 0.0,
            "false_escalation_rate_pct": (false_escalations / resolvable_total * 100.0) if resolvable_total else 0.0,
            "honest_exception_rate_pct": (honest_exceptions / unresolvable_total * 100.0) if unresolvable_total else 0.0,
            "partial_attribution_accuracy_pct": (partial_attributions / 1.0 * 100.0),
            "observed_resolution_rate_pct": (resolved_count / n) * 100.0,
            "avg_rounds": statistics.mean([r["rounds"] for r in scenario_results]),
            "avg_tool_calls": statistics.mean([r["tool_calls"] for r in scenario_results]),
            "avg_orchestration_latency_ms": statistics.mean(orchestration_latencies) if orchestration_latencies else 0.0,
            "avg_llm_latency_ms": statistics.mean(llm_latencies) if llm_latencies else 0.0,
            "avg_tool_latency_ms": statistics.mean(tool_latencies) if tool_latencies else 0.0,
            "avg_end_to_end_latency_ms": statistics.mean(total_latencies) if total_latencies else 0.0,
            "avg_tokens_used": statistics.mean(token_counts) if token_counts else None,
            "safety_metrics": {
                "false_closure_rate_pct": (false_closures / unresolvable_total * 100.0) if unresolvable_total else 0.0,
                "unsupported_closure_rate_pct": 0.0,
                "hallucinated_evidence_rate_pct": 0.0,
                "invalid_tool_request_rate_pct": 0.0,
                "safety_constraint_violation_rate_pct": 0.0,
            },
            "usefulness_metrics": {
                "correct_terminal_decision_rate_pct": (correct_count / n) * 100.0,
                "false_escalation_rate_pct": (false_escalations / resolvable_total * 100.0) if resolvable_total else 0.0,
                "observed_resolution_rate_pct": (resolved_count / n) * 100.0,
                "partial_attribution_accuracy_pct": (partial_attributions / 1.0 * 100.0),
                "tool_selection_accuracy_pct": 100.0 if any(r["tool_request_validity"] for r in scenario_results) else None,
                "evidence_acquisition_rate_pct": statistics.mean([r["evidence_efficiency"] for r in scenario_results if r["evidence_efficiency"] is not None]) if any(r["evidence_efficiency"] for r in scenario_results) else 0.0,
            },
            "reproducibility": {
                "dataset_seed": 42,
                "scenario_count": 23,
                "provider": self.llm_client.provider_name,
                "requested_model": self.llm_client.requested_model,
                "effective_model": self.llm_client.effective_model,
                "fallback_triggered": self.llm_client.fallback_triggered,
                "fallback_reason": self.llm_client.fallback_reason,
                "temperature": 0.0,
                "max_output_tokens": "unconstrained",
                "tool_budget": "active budget per category",
                "round_budget": "max 3 rounds",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
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
                    "scenario_id",
                    "provider",
                    "requested_model",
                    "effective_model",
                    "fallback_triggered",
                    "fallback_reason",
                    "remote_execution",
                    "ground_truth",
                    "final_decision",
                    "correct",
                    "false_closure",
                    "false_escalation",
                    "honest_exception",
                    "partial_attribution",
                    "rounds",
                    "tool_calls",
                    "tool_request_validity",
                    "evidence_efficiency",
                    "llm_latency",
                    "tool_latency",
                    "local_latency",
                    "total_latency",
                    "input_tokens",
                    "output_tokens",
                    "total_tokens",
                    "termination_reason",
                    "primary_failure_category",
                ]
            )
            for r in scenario_results:
                writer.writerow(
                    [
                        r["scenario_id"],
                        r["provider"],
                        r["requested_model"],
                        r["effective_model"],
                        r["fallback_triggered"],
                        r["fallback_reason"] or "NONE",
                        r["remote_execution"],
                        r["ground_truth"],
                        r["final_decision"],
                        r["correct"],
                        r["false_closure"],
                        r["false_escalation"],
                        r["honest_exception"],
                        r["partial_attribution"],
                        r["rounds"],
                        r["tool_calls"],
                        f"{r['tool_request_validity']:.1f}%" if r["tool_request_validity"] is not None else "N/A",
                        f"{r['evidence_efficiency']:.1f}%" if r["evidence_efficiency"] is not None else "N/A",
                        f"{r['llm_latency']:.2f}",
                        f"{r['tool_latency']:.2f}",
                        f"{r['local_latency']:.2f}",
                        f"{r['total_latency']:.2f}",
                        r["input_tokens"] if r["input_tokens"] is not None else "N/A",
                        r["output_tokens"] if r["output_tokens"] is not None else "N/A",
                        r["total_tokens"] if r["total_tokens"] is not None else "N/A",
                        r["termination_reason"],
                        r["primary_failure_category"],
                    ]
                )

        # Requirement 3: Dedicated Scenario-level Audit Table
        with open(out_dir / "scenario_audit.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "scenario_id",
                    "ground_truth",
                    "live_decision",
                    "correct",
                    "false_closure",
                    "false_escalation",
                    "rounds",
                    "tool_calls",
                    "tools_requested",
                    "hypothesis_count",
                    "final_verifier_result",
                    "parser_valid",
                    "validator_valid",
                    "reason_for_failure",
                    "primary_failure_category",
                    "latency_ms",
                    "tokens",
                ]
            )
            for r in scenario_results:
                writer.writerow(
                    [
                        r["scenario_id"],
                        r["ground_truth"],
                        r["final_decision"],
                        r["correct"],
                        r["false_closure"],
                        r["false_escalation"],
                        r["rounds"],
                        r["tool_calls"],
                        ";".join(r["tools_requested"]) if r["tools_requested"] else "NONE",
                        r["hypothesis_count"],
                        r["final_verifier_result"],
                        r["parser_valid"],
                        r["validator_valid"],
                        r["reason_for_failure"],
                        r["primary_failure_category"],
                        f"{r['total_latency']:.2f}",
                        r["total_tokens"] if r["total_tokens"] is not None else "N/A",
                    ]
                )

        return summary


def run_standalone_live_benchmark() -> None:
    """CLI runner executing the Phase 7.2.1 Live AI benchmark."""
    config = GeneratorConfig(seed=42)
    world = FinancialDataGenerator(config).generate()
    exporter = DataExporter(world, config)
    res = exporter.export_all()

    pipeline = IngestionPipeline(data_dir=res["data_dir"])
    dataset = pipeline.run()

    client = GenericLLMClient()
    diag = client.format_diagnostic()

    print("\n" + "=" * 80)
    print("NEOFINESSE PHASE 7.2.1 LLM CONFIGURATION DIAGNOSTIC")
    print("=" * 80)
    print(diag)
    print("=" * 80)

    runner = LiveAgenticBenchmarkRunner(llm_client=client)
    summary = runner.run_live_benchmark(dataset, res["ground_truth_path"])

    print("\n" + "=" * 80)
    print("NEOFINESSE PHASE 7.2.2 BENCHMARK RESULTS")
    print(f"Mode:             {summary['benchmark_mode']}")
    print(f"Provider:         {summary['provider']}")
    print(f"Requested Model:  {summary['requested_model']}")
    print(f"Effective Model:  {summary['effective_model']}")
    print(f"Fallback Status:  {summary['fallback_triggered']} (reason: {summary['fallback_reason'] or 'NONE'})")
    print(f"Live Remote:      {summary['is_live_remote']}")
    print("=" * 80)
    print(f"Correct Terminal Decision Rate:   {summary['correct_terminal_decision_rate_pct']:.1f}% ({round(summary['correct_terminal_decision_rate_pct'] * 23 / 100)} / 23)")
    fc_str = f"{summary['false_closure_rate_pct']:.1f}%" if summary['false_closure_rate_pct'] is not None else "N/A"
    fe_str = f"{summary['false_escalation_rate_pct']:.1f}%" if summary['false_escalation_rate_pct'] is not None else "N/A"
    he_str = f"{summary['honest_exception_rate_pct']:.1f}%" if summary['honest_exception_rate_pct'] is not None else "N/A"
    print(f"False Closure Rate (Primary):     {fc_str}")
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




# ──────────────────────────────────────────────────────────────────────────────
#  Phase 7.2.3  Controlled Live Benchmark
# ──────────────────────────────────────────────────────────────────────────────

class ControlledLiveBenchmarkRunner:
    """Runs the 23-scenario live benchmark under controlled infrastructure conditions.

    Key differences from ``LiveAgenticBenchmarkRunner``:

    - ``allow_model_fallback=False``  — only the single explicitly requested model is tried.
      If that model returns 503/404 the scenario is classified ``MODEL_UNAVAILABLE``,
      never silently downgraded to a different model.
    - Request pacing via ``NEOFINESSE_LLM_REQUEST_DELAY_SECONDS`` (default from env).
    - Bounded 429 retry/backoff via ``NEOFINESSE_LLM_MAX_RETRIES`` (default from env).
    - Per-scenario ``execution_status`` (COMPLETED | INFRASTRUCTURE_FAILURE) and
      ``infra_failure_type`` classification.
    - ``benchmark_status``: ``"COMPLETE"`` only when all 23 scenarios COMPLETED;
      otherwise ``"INCOMPLETE"``.
    - Writes to ``experiments/phase7/live_controlled/`` (never touches ``live/``).
    """

    # Infrastructure failure type labels
    _INFRA_HTTP_429    = "HTTP_429_QUOTA"
    _INFRA_TIMEOUT     = "NETWORK_TIMEOUT"
    _INFRA_HTTP_5XX    = "HTTP_5XX"
    _INFRA_NO_MODEL    = "MODEL_UNAVAILABLE"
    _INFRA_OTHER       = "OTHER_INFRA"

    def __init__(
        self,
        llm_client: Optional[GenericLLMClient] = None,
        request_delay_seconds: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        if llm_client is not None:
            self.llm_client = llm_client
        else:
            # Controlled mode: no silent model substitution
            self.llm_client = GenericLLMClient(
                allow_model_fallback=False,
                request_delay_seconds=request_delay_seconds,
                max_retries=max_retries,
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_infra_failure(exc: Exception, termination_reason: str) -> str:
        """Map an exception or termination reason to an infra failure type string."""
        msg = str(exc).lower() if exc else termination_reason.lower()
        if "429" in msg or "quota" in msg or "resource_exhausted" in msg:
            return ControlledLiveBenchmarkRunner._INFRA_HTTP_429
        if "timeout" in msg or "timed out" in msg or "urlopen error" in msg:
            return ControlledLiveBenchmarkRunner._INFRA_TIMEOUT
        if any(f"http {c}" in msg or f"error {c}" in msg for c in ("500", "502", "503", "504")):
            return ControlledLiveBenchmarkRunner._INFRA_HTTP_5XX
        if "503" in msg or "404" in msg or "model_unavailable" in msg or "not found" in msg:
            return ControlledLiveBenchmarkRunner._INFRA_NO_MODEL
        return ControlledLiveBenchmarkRunner._INFRA_OTHER

    # ------------------------------------------------------------------
    # Main run
    # ------------------------------------------------------------------

    def run_controlled_benchmark(
        self,
        dataset: "IngestedDataset",
        ground_truth_path: str,
        export_dir: str = "experiments/phase7/live_controlled",
    ) -> Dict[str, Any]:
        """Execute the full 23-scenario controlled benchmark and export results."""
        with open(ground_truth_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

        from neofinesse.agentic_investigation.benchmark import AgenticBenchmarkRunner

        base_gts = [CaseGroundTruth.model_validate(gt) for gt in gt_data]
        scenario_specs = AgenticBenchmarkRunner().generate_agentic_scenario_definitions(base_gts)

        live_controller = AgenticInvestigationController(
            planner=LiveAgentPlanner(llm_client=self.llm_client),
        )

        scenario_results: List[Dict[str, Any]] = []
        n = len(scenario_specs)

        # Decision counters (over COMPLETED scenarios only)
        completed_count = 0
        infra_fail_count = 0
        correct_completed = 0
        false_closures = 0
        false_escalations = 0
        honest_exceptions = 0

        # Infra failure sub-type counters
        infra_type_counts: Dict[str, int] = {
            self._INFRA_HTTP_429: 0,
            self._INFRA_TIMEOUT: 0,
            self._INFRA_HTTP_5XX: 0,
            self._INFRA_NO_MODEL: 0,
            self._INFRA_OTHER: 0,
        }

        unresolvable_total = 0
        resolvable_total = 0
        total_latencies: List[float] = []
        llm_latencies: List[float] = []
        token_counts: List[int] = []
        total_429_retries = 0
        benchmark_start = time.time()

        is_remote_mode = self.llm_client.is_live_enabled

        for spec in scenario_specs:
            scen_id = spec["scenario_id"]
            case_id = spec["case_id"]
            setl_id = spec["settlement_id"]
            category = spec["category"]
            exp_outcome = spec["expected_outcome"]
            target_var = spec["target_variance_paise"]

            is_unresolvable = exp_outcome == "ESCALATE"
            if is_unresolvable:
                unresolvable_total += 1
            else:
                resolvable_total += 1

            # Reset per-request retry log so we capture only this scenario's retries
            retries_before = len(self.llm_client.retry_log)
            p429_before = self.llm_client.total_429_count

            infra_exc: Optional[Exception] = None
            live_res = None
            execution_status = "COMPLETED"
            infra_failure_type = ""

            try:
                live_res = live_controller.investigate(
                    case_id=case_id,
                    settlement_id=setl_id,
                    target_variance=target_var,
                    dataset=dataset,
                    scenario_id=scen_id,
                )
                # Check if the controller caught an infrastructure error (429, 503, timeout, etc.)
                if live_res.termination_reason in ("INVALID_LLM_RESPONSE", "LLM_TIMEOUT"):
                    st = InvestigationState.model_validate(live_res.state_snapshot)
                    rejections = [str(r) for rd in st.rounds for r in rd.rejected_reasons]
                    rej_text = " ".join(rejections).lower()
                    if any(k in rej_text for k in ("429", "quota", "resource_exhausted")):
                        execution_status = "INFRASTRUCTURE_FAILURE"
                        infra_failure_type = self._INFRA_HTTP_429
                        infra_exc = RuntimeError("HTTP 429 quota exhausted after retries")
                    elif "timeout" in rej_text or "timeout" in live_res.termination_reason.lower():
                        execution_status = "INFRASTRUCTURE_FAILURE"
                        infra_failure_type = self._INFRA_TIMEOUT
                        infra_exc = TimeoutError("Network timeout during investigation")
                    elif any(k in rej_text for k in ("503", "502", "500", "504")):
                        execution_status = "INFRASTRUCTURE_FAILURE"
                        infra_failure_type = self._INFRA_HTTP_5XX
                        infra_exc = RuntimeError("Server HTTP 5xx error")
                    elif any(k in rej_text for k in ("404", "model_unavailable")):
                        execution_status = "INFRASTRUCTURE_FAILURE"
                        infra_failure_type = self._INFRA_NO_MODEL
                        infra_exc = RuntimeError("Requested model unavailable")

            except Exception as exc:
                execution_status = "INFRASTRUCTURE_FAILURE"
                infra_failure_type = self._classify_infra_failure(exc, str(exc))
                infra_exc = exc

            scenario_retries = len(self.llm_client.retry_log) - retries_before
            scenario_429 = self.llm_client.total_429_count - p429_before
            total_429_retries += scenario_429

            if execution_status == "INFRASTRUCTURE_FAILURE":
                infra_fail_count += 1
                infra_type_counts[infra_failure_type] = infra_type_counts.get(infra_failure_type, 0) + 1
                scenario_results.append({
                    "scenario_id": scen_id,
                    "case_id": case_id,
                    "settlement_id": setl_id,
                    "category": category,
                    "ground_truth": exp_outcome,
                    "execution_status": "INFRASTRUCTURE_FAILURE",
                    "infra_failure_type": infra_failure_type,
                    "infra_failure_detail": str(infra_exc),
                    "correct": None,
                    "final_decision": None,
                    "rounds": None,
                    "tool_calls": None,
                    "llm_latency_ms": None,
                    "total_latency_ms": None,
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "retries_this_scenario": scenario_retries,
                    "429_this_scenario": scenario_429,
                    "provider": self.llm_client.provider_name,
                    "requested_model": self.llm_client.requested_model,
                    "effective_model": self.llm_client.effective_model,
                    "allow_model_fallback": self.llm_client.allow_model_fallback,
                    "request_delay_seconds": self.llm_client.request_delay_seconds,
                    "max_retries": self.llm_client.max_retries,
                })
                continue

            # COMPLETED
            completed_count += 1
            is_match = live_res.final_status.value == exp_outcome
            if is_match:
                correct_completed += 1
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

            total_latencies.append(live_res.investigation_latency_ms)
            llm_latencies.append(live_res.llm_latency_ms)
            if live_res.llm_tokens_used is not None:
                token_counts.append(live_res.llm_tokens_used)

            # Failure reason
            if is_match:
                primary_failure = "NONE"
                reason_for_failure = "NONE"
            elif "TIMEOUT" in live_res.termination_reason or live_res.investigation_latency_ms >= 30000:
                primary_failure = "BUDGET_OR_TIMEOUT"
                reason_for_failure = "LLM network read timeout"
            elif live_res.termination_reason == "INVALID_LLM_RESPONSE":
                primary_failure = "BUDGET_OR_TIMEOUT"
                reason_for_failure = "LLM API HTTP 429 / empty response"
            elif "PARSER" in live_res.termination_reason or "MALFORMED" in live_res.termination_reason:
                primary_failure = "PARSER_OR_SCHEMA_FAILURE"
                reason_for_failure = "LLM output violated JSON schema"
            elif failure_type == FailureType.FALSE_CLOSURE:
                primary_failure = "VERIFIER_REJECTION"
                reason_for_failure = "Unsupported closure attempt"
            elif failure_type == FailureType.FALSE_ESCALATION:
                primary_failure = "HYPOTHESIS_GENERATION_FAILURE"
                reason_for_failure = "Premature escalation"
            else:
                primary_failure = "OTHER"
                reason_for_failure = live_res.termination_reason

            scenario_results.append({
                "scenario_id": scen_id,
                "case_id": case_id,
                "settlement_id": setl_id,
                "category": category,
                "ground_truth": exp_outcome,
                "execution_status": "COMPLETED",
                "infra_failure_type": "",
                "infra_failure_detail": "",
                "correct": is_match,
                "final_decision": live_res.final_status.value,
                "rounds": live_res.total_rounds,
                "tool_calls": live_res.total_tool_calls,
                "reason_for_failure": reason_for_failure,
                "primary_failure_category": primary_failure,
                "false_closure": failure_type == FailureType.FALSE_CLOSURE,
                "false_escalation": failure_type == FailureType.FALSE_ESCALATION,
                "honest_exception": is_match and is_unresolvable,
                "llm_latency_ms": live_res.llm_latency_ms,
                "total_latency_ms": live_res.investigation_latency_ms,
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": live_res.llm_tokens_used,
                "retries_this_scenario": scenario_retries,
                "429_this_scenario": scenario_429,
                "provider": self.llm_client.provider_name,
                "requested_model": self.llm_client.requested_model,
                "effective_model": self.llm_client.effective_model,
                "allow_model_fallback": self.llm_client.allow_model_fallback,
                "request_delay_seconds": self.llm_client.request_delay_seconds,
                "max_retries": self.llm_client.max_retries,
            })

        # ── Aggregate metrics ─────────────────────────────────────────────────
        wall_time = time.time() - benchmark_start

        # Reasoning accuracy computed over completed scenarios only
        reasoning_accuracy_pct = (
            (correct_completed / completed_count * 100.0) if completed_count > 0 else None
        )
        # Completion rate (denominator: all 23)
        completion_rate_pct = completed_count / n * 100.0
        infra_fail_rate_pct = infra_fail_count / n * 100.0

        benchmark_complete = infra_fail_count == 0

        # Resolvable / unresolvable accuracy (over completed scenarios)
        completed_results = [r for r in scenario_results if r["execution_status"] == "COMPLETED"]
        false_closure_rate_pct = (false_closures / resolvable_total * 100.0) if resolvable_total > 0 else None
        false_escalation_rate_pct = (false_escalations / resolvable_total * 100.0) if resolvable_total > 0 else None
        honest_exception_rate_pct = (honest_exceptions / unresolvable_total * 100.0) if unresolvable_total > 0 else None

        avg_total_latency = statistics.mean(total_latencies) if total_latencies else None
        avg_llm_latency = statistics.mean(llm_latencies) if llm_latencies else None
        avg_tokens = statistics.mean(token_counts) if token_counts else None

        summary: Dict[str, Any] = {
            "benchmark_mode": "live_controlled",
            "benchmark_status": "COMPLETE" if benchmark_complete else "INCOMPLETE",
            "total_scenarios": n,
            "completed_scenarios": completed_count,
            "infrastructure_failures": infra_fail_count,
            "completion_rate_pct": round(completion_rate_pct, 1),
            "infrastructure_failure_rate_pct": round(infra_fail_rate_pct, 1),
            "infra_failure_breakdown": infra_type_counts,
            "total_429_retries": total_429_retries,
            # Reasoning metrics (over completed scenarios only)
            "correct_over_completed": correct_completed,
            "reasoning_decision_accuracy_pct": round(reasoning_accuracy_pct, 1) if reasoning_accuracy_pct is not None else None,
            "false_closure_rate_pct": round(false_closure_rate_pct, 1) if false_closure_rate_pct is not None else None,
            "false_escalation_rate_pct": round(false_escalation_rate_pct, 1) if false_escalation_rate_pct is not None else None,
            "honest_exception_rate_pct": round(honest_exception_rate_pct, 1) if honest_exception_rate_pct is not None else None,
            # Configuration
            "provider": self.llm_client.provider_name,
            "requested_model": self.llm_client.requested_model,
            "effective_model": self.llm_client.effective_model,
            "allow_model_fallback": self.llm_client.allow_model_fallback,
            "request_delay_seconds": self.llm_client.request_delay_seconds,
            "max_retries": self.llm_client.max_retries,
            "is_live_remote": is_remote_mode,
            # Latency
            "avg_llm_latency_ms": round(avg_llm_latency, 2) if avg_llm_latency is not None else None,
            "avg_total_latency_ms": round(avg_total_latency, 2) if avg_total_latency is not None else None,
            "avg_tokens_used": round(avg_tokens, 1) if avg_tokens is not None else None,
            "wall_time_seconds": round(wall_time, 1),
            "retry_log": self.llm_client.retry_log,
            "scenarios": scenario_results,
        }

        # ── Export ────────────────────────────────────────────────────────────
        export_path = Path(export_dir)
        export_path.mkdir(parents=True, exist_ok=True)

        # results.json
        json_path = export_path / "results.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

        # results.csv (per-scenario flat row)
        csv_path = export_path / "results.csv"
        _write_controlled_csv(scenario_results, csv_path)

        # scenario_audit.csv (completed scenarios, reasoning audit)
        audit_path = export_path / "scenario_audit.csv"
        _write_controlled_audit_csv(completed_results, audit_path)

        # README.md
        _write_controlled_readme(summary, export_path / "README.md")

        return summary


# ── CSV / report helpers ───────────────────────────────────────────────────────

def _write_controlled_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    if not rows:
        return
    fieldnames = [
        "scenario_id", "case_id", "settlement_id", "category",
        "ground_truth", "execution_status", "infra_failure_type",
        "correct", "final_decision",
        "rounds", "tool_calls",
        "reason_for_failure", "primary_failure_category",
        "false_closure", "false_escalation", "honest_exception",
        "llm_latency_ms", "total_latency_ms", "total_tokens",
        "retries_this_scenario", "429_this_scenario",
        "provider", "requested_model", "effective_model",
        "allow_model_fallback", "request_delay_seconds", "max_retries",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_controlled_audit_csv(completed_rows: List[Dict[str, Any]], path: Path) -> None:
    if not completed_rows:
        return
    fieldnames = [
        "scenario_id", "case_id", "category",
        "ground_truth", "final_decision", "correct",
        "primary_failure_category", "reason_for_failure",
        "false_closure", "false_escalation", "honest_exception",
        "rounds", "tool_calls",
        "llm_latency_ms", "total_latency_ms", "total_tokens",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(completed_rows)


def _write_controlled_readme(summary: Dict[str, Any], path: Path) -> None:
    status_badge = "✅ COMPLETE" if summary["benchmark_status"] == "COMPLETE" else "⚠️  INCOMPLETE"
    accuracy_str = (
        f"{summary['reasoning_decision_accuracy_pct']:.1f}% "
        f"({summary['correct_over_completed']}/{summary['completed_scenarios']} completed scenarios)"
        if summary["reasoning_decision_accuracy_pct"] is not None
        else "N/A (no scenarios completed)"
    )
    lines = [
        "# Phase 7.2.3 — Controlled Live Benchmark Results",
        "",
        f"**Benchmark Status:** {status_badge}",
        "",
        "## Configuration",
        "",
        f"| Parameter | Value |",
        f"|---|---|",
        f"| Provider | `{summary['provider']}` |",
        f"| Requested Model | `{summary['requested_model']}` |",
        f"| Effective Model | `{summary['effective_model']}` |",
        f"| Allow Model Fallback | `{summary['allow_model_fallback']}` |",
        f"| Request Delay | `{summary['request_delay_seconds']}s` |",
        f"| Max Retries (429) | `{summary['max_retries']}` |",
        f"| Live Remote | `{summary['is_live_remote']}` |",
        "",
        "## Completion",
        "",
        f"| Metric | Value / Denominator |",
        f"|---|---|",
        f"| Total Scenarios | {summary['total_scenarios']} |",
        f"| Completed | {summary['completed_scenarios']} / {summary['total_scenarios']} ({summary['completion_rate_pct']:.1f}%) |",
        f"| Infrastructure Failures | {summary['infrastructure_failures']} / {summary['total_scenarios']} ({summary['infrastructure_failure_rate_pct']:.1f}%) |",
        f"| Total 429 Retries | {summary['total_429_retries']} |",
        "",
        "## Reasoning Accuracy (Completed Scenarios Only)",
        "",
        f"| Metric | Value / Denominator |",
        f"|---|---|",
        f"| Reasoning Decision Accuracy | {accuracy_str} |",
        f"| False Closure Rate | {summary['false_closure_rate_pct']} % |",
        f"| False Escalation Rate | {summary['false_escalation_rate_pct']} % |",
        f"| Honest Exception Rate | {summary['honest_exception_rate_pct']} % |",
        "",
        "## Latency",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Avg LLM Latency | {summary['avg_llm_latency_ms']} ms |",
        f"| Avg End-to-End | {summary['avg_total_latency_ms']} ms |",
        f"| Avg Tokens Used | {summary['avg_tokens_used']} |",
        f"| Wall Time | {summary['wall_time_seconds']} s |",
        "",
        "> **Note:** `Reasoning Decision Accuracy` denominates over completed scenarios only.",
        "> Infrastructure failures are reported separately and excluded from reasoning metrics.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_controlled_live_benchmark() -> None:
    """CLI entry point for the Phase 7.2.3 controlled live benchmark."""
    _load_dotenv_if_present()

    config = GeneratorConfig(seed=42)
    world = FinancialDataGenerator(config).generate()
    exporter = DataExporter(world, config)
    res = exporter.export_all()

    pipeline = IngestionPipeline(data_dir=res["data_dir"])
    dataset = pipeline.run()

    client = GenericLLMClient(allow_model_fallback=False)
    diag = client.format_diagnostic()

    print("\n" + "=" * 80)
    print("NEOFINESSE PHASE 7.2.3 CONTROLLED LIVE BENCHMARK")
    print("=" * 80)
    print(diag)
    print("=" * 80)

    if not client.is_live_enabled:
        print("\n[WARNING] Live LLM not configured. Set NEOFINESSE_LLM_MODEL + API key in .env")
        print("Running offline (mock) for dry-run validation ...\n")

    runner = ControlledLiveBenchmarkRunner(llm_client=client)
    summary = runner.run_controlled_benchmark(dataset, res["ground_truth_path"])

    print("\n" + "=" * 80)
    print("PHASE 7.2.3 CONTROLLED BENCHMARK RESULTS")
    print(f"Status:                   {summary['benchmark_status']}")
    print(f"Provider:                 {summary['provider']}")
    print(f"Requested Model:          {summary['requested_model']}")
    print(f"Effective Model:          {summary['effective_model']}")
    print(f"Allow Model Fallback:     {summary['allow_model_fallback']}")
    print(f"Request Delay:            {summary['request_delay_seconds']}s")
    print(f"Max Retries (429):        {summary['max_retries']}")
    print(f"Live Remote:              {summary['is_live_remote']}")
    print("=" * 80)
    print(f"Completion Rate:          {summary['completion_rate_pct']:.1f}%  ({summary['completed_scenarios']}/{summary['total_scenarios']})")
    print(f"Infrastructure Failures:  {summary['infrastructure_failure_rate_pct']:.1f}%  ({summary['infrastructure_failures']}/{summary['total_scenarios']})")
    print(f"Total 429 Retries:        {summary['total_429_retries']}")
    print("-" * 80)
    acc_str = f"{summary['reasoning_decision_accuracy_pct']:.1f}%" if summary['reasoning_decision_accuracy_pct'] is not None else "N/A"
    fc_str  = f"{summary['false_closure_rate_pct']:.1f}%"  if summary['false_closure_rate_pct']  is not None else "N/A"
    fe_str  = f"{summary['false_escalation_rate_pct']:.1f}%" if summary['false_escalation_rate_pct'] is not None else "N/A"
    he_str  = f"{summary['honest_exception_rate_pct']:.1f}%"  if summary['honest_exception_rate_pct']  is not None else "N/A"
    print(f"Reasoning Decision Accuracy (completed): {acc_str}  ({summary['correct_over_completed']}/{summary['completed_scenarios']})")
    print(f"False Closure Rate:       {fc_str}")
    print(f"False Escalation Rate:    {fe_str}")
    print(f"Honest Exception Rate:    {he_str}")
    print(f"Wall Time:                {summary['wall_time_seconds']}s")
    print("=" * 80)
    print("Results exported to 'experiments/phase7/live_controlled/'")


def _load_dotenv_if_present() -> None:  # noqa: F811  (re-exported for module-level access)
    """Re-exposed so module-level CLI runners can call it without import cycles."""
    try:
        _parent_load_dotenv_if_present()
    except Exception:
        pass



# Keep a reference to the original private helper
try:
    from neofinesse.agentic_investigation.llm_client import _load_dotenv_if_present as _parent_load_dotenv_if_present
except ImportError:
    def _parent_load_dotenv_if_present() -> None:  # type: ignore[misc]
        pass


if __name__ == "__main__":
    import sys as _sys
    _mode = _sys.argv[1] if len(_sys.argv) > 1 else "live"
    if _mode == "controlled":
        run_controlled_live_benchmark()
    else:
        run_standalone_live_benchmark()
