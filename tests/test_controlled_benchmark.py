"""
tests/test_controlled_benchmark.py
Phase 7.2.3 — Controlled benchmark infrastructure unit tests.

Coverage targets:
- GenericLLMClient: request pacing, 429 backoff, allow_model_fallback=False
- ControlledLiveBenchmarkRunner: offline execution, infra-failure classification,
  benchmark_status COMPLETE vs INCOMPLETE, CSV/README export
"""
from __future__ import annotations

import json
import time
import unittest
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from neofinesse.agentic_investigation.llm_client import GenericLLMClient
from neofinesse.agentic_investigation.live_benchmark import (
    ControlledLiveBenchmarkRunner,
    _write_controlled_csv,
    _write_controlled_audit_csv,
    _write_controlled_readme,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_mock_http_error(code: int, msg: str = "", retry_after: Optional[str] = None) -> urllib.error.HTTPError:
    """Build a minimal HTTPError with an optional Retry-After header."""
    headers = {}
    if retry_after:
        headers["Retry-After"] = retry_after
    mock_hdr = MagicMock()
    mock_hdr.get = lambda k, default=None: headers.get(k, default)

    err = urllib.error.HTTPError(
        url="https://example.com",
        code=code,
        msg=msg,
        hdrs=mock_hdr,
        fp=None,
    )
    err.headers = mock_hdr
    return err


def _offline_client(**kwargs) -> GenericLLMClient:
    """Return a GenericLLMClient that is always in mock/offline mode."""
    # No API key → provider falls back to mock
    client = GenericLLMClient(**kwargs)
    return client


# ─── GenericLLMClient: new constructor fields ──────────────────────────────────

class TestGenericLLMClientNewFields:
    def test_defaults_without_env(self, monkeypatch):
        monkeypatch.setattr("neofinesse.agentic_investigation.llm_client._load_dotenv_if_present", lambda: None)
        monkeypatch.delenv("NEOFINESSE_LLM_REQUEST_DELAY_SECONDS", raising=False)
        monkeypatch.delenv("NEOFINESSE_LLM_MAX_RETRIES", raising=False)
        client = _offline_client()
        assert client.request_delay_seconds == 0.0  # default from env missing → 0
        assert client.max_retries == 3              # default from env missing → 3
        assert client.allow_model_fallback is True
        assert isinstance(client.retry_log, list)
        assert client.total_429_count == 0
        assert client.total_timeout_count == 0
        assert client._last_request_time == 0.0

    def test_env_overrides(self, monkeypatch):
        monkeypatch.setenv("NEOFINESSE_LLM_REQUEST_DELAY_SECONDS", "7")
        monkeypatch.setenv("NEOFINESSE_LLM_MAX_RETRIES", "5")
        client = _offline_client()
        assert client.request_delay_seconds == 7.0
        assert client.max_retries == 5

    def test_constructor_params_override_env(self, monkeypatch):
        monkeypatch.setenv("NEOFINESSE_LLM_REQUEST_DELAY_SECONDS", "9")
        monkeypatch.setenv("NEOFINESSE_LLM_MAX_RETRIES", "9")
        client = _offline_client(request_delay_seconds=2.0, max_retries=1, allow_model_fallback=False)
        assert client.request_delay_seconds == 2.0
        assert client.max_retries == 1
        assert client.allow_model_fallback is False

    def test_get_diagnostic_includes_new_fields(self):
        client = _offline_client(request_delay_seconds=3.0, max_retries=2, allow_model_fallback=False)
        diag = client.get_diagnostic()
        assert "allow_model_fallback" in diag
        assert "request_delay_seconds" in diag
        assert "max_retries" in diag
        assert diag["allow_model_fallback"] is False
        assert diag["request_delay_seconds"] == 3.0
        assert diag["max_retries"] == 2

    def test_format_diagnostic_includes_new_fields(self):
        client = _offline_client(request_delay_seconds=4.0, max_retries=3, allow_model_fallback=True)
        text = client.format_diagnostic()
        assert "Allow Model Fallback" in text
        assert "Request Delay" in text
        assert "Max Retries" in text


# ─── Request pacing ────────────────────────────────────────────────────────────

class TestRequestPacing:
    def test_no_sleep_when_delay_zero(self):
        client = _offline_client(request_delay_seconds=0.0)
        client._last_request_time = time.monotonic() - 0.001  # simulate recent call
        with patch("time.sleep") as mock_sleep:
            client._apply_request_pacing()
            mock_sleep.assert_not_called()

    def test_no_sleep_on_first_call(self):
        client = _offline_client(request_delay_seconds=4.0)
        assert client._last_request_time == 0.0
        with patch("time.sleep") as mock_sleep:
            client._apply_request_pacing()
            mock_sleep.assert_not_called()

    def test_sleep_when_elapsed_less_than_delay(self, monkeypatch):
        client = _offline_client(request_delay_seconds=4.0)
        # Simulate a call that happened 1 second ago
        client._last_request_time = time.monotonic() - 1.0
        sleep_calls: List[float] = []
        monkeypatch.setattr("time.sleep", lambda s: sleep_calls.append(s))
        client._apply_request_pacing()
        assert len(sleep_calls) == 1
        assert sleep_calls[0] == pytest.approx(3.0, abs=0.2)

    def test_no_sleep_when_enough_time_has_passed(self):
        client = _offline_client(request_delay_seconds=2.0)
        client._last_request_time = time.monotonic() - 5.0  # 5s ago → no wait
        with patch("time.sleep") as mock_sleep:
            client._apply_request_pacing()
            mock_sleep.assert_not_called()

    def test_pacing_updates_last_request_time(self):
        # Use a tiny non-zero delay so the update branch is entered
        client = _offline_client(request_delay_seconds=0.001)
        before = time.monotonic()
        client._apply_request_pacing()  # first call: no sleep, but sets _last_request_time
        assert client._last_request_time >= before


# ─── 429 backoff logic ─────────────────────────────────────────────────────────

class TestRetry429Logic:
    def _live_client(self, **kwargs) -> GenericLLMClient:
        """Minimal live-enabled client stub (doesn't actually call network)."""
        client = _offline_client(
            provider="gemini",
            model="gemini-3.8-flash",
            api_key="fake-key-123456",
            **kwargs,
        )
        # Force is_live_enabled = True so dispatch runs
        client._force_live = True
        return client

    def test_429_increments_counter_and_retries(self):
        client = self._live_client(max_retries=2, request_delay_seconds=0)

        call_count = 0
        def _mock_post(*a, **kw):
            nonlocal call_count
            call_count += 1
            raise _make_mock_http_error(429)

        with patch.object(client, "_determine_endpoint", return_value="https://fake.endpoint"):
            with patch("urllib.request.urlopen", side_effect=_mock_post):
                with patch("time.sleep"):  # suppress actual sleeping
                    with pytest.raises(RuntimeError, match="429"):
                        client._dispatch_http_request_with_tokens("prompt")

        # 1 initial + 2 retries = 3 calls
        assert call_count == 3
        assert client.total_429_count == 3

    def test_429_backoff_uses_retry_after_header(self):
        client = self._live_client(max_retries=1, request_delay_seconds=0)

        sleep_calls: List[float] = []

        def _mock_post(*a, **kw):
            raise _make_mock_http_error(429, retry_after="15")

        with patch.object(client, "_determine_endpoint", return_value="https://fake.endpoint"):
            with patch("urllib.request.urlopen", side_effect=_mock_post):
                with patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)):
                    with pytest.raises(RuntimeError, match="429"):
                        client._dispatch_http_request_with_tokens("prompt")

        # Should have used Retry-After=15 for first retry
        assert sleep_calls[0] == pytest.approx(15.0)

    def test_429_exponential_backoff_without_retry_after(self):
        client = self._live_client(max_retries=2, request_delay_seconds=0)

        sleep_calls: List[float] = []

        def _mock_post(*a, **kw):
            raise _make_mock_http_error(429)

        with patch.object(client, "_determine_endpoint", return_value="https://fake.endpoint"):
            with patch("urllib.request.urlopen", side_effect=_mock_post):
                with patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)):
                    with pytest.raises(RuntimeError, match="429"):
                        client._dispatch_http_request_with_tokens("prompt")

        # Attempt 1 → backoff 2^1=2, attempt 2 → backoff 2^2=4
        assert sleep_calls[0] == pytest.approx(2.0)
        assert sleep_calls[1] == pytest.approx(4.0)

    def test_429_retry_log_populated(self):
        client = self._live_client(max_retries=1, request_delay_seconds=0)

        def _mock_post(*a, **kw):
            raise _make_mock_http_error(429)

        with patch.object(client, "_determine_endpoint", return_value="https://fake.endpoint"):
            with patch("urllib.request.urlopen", side_effect=_mock_post):
                with patch("time.sleep"):
                    with pytest.raises(RuntimeError):
                        client._dispatch_http_request_with_tokens("prompt")

        assert len(client.retry_log) >= 1
        entry = client.retry_log[0]
        assert entry["status"] == 429
        assert entry["reason"] == "RESOURCE_EXHAUSTED"
        assert "backoff_seconds" in entry

    def test_succeeds_after_one_429(self):
        client = self._live_client(max_retries=1, request_delay_seconds=0)

        call_count = 0
        def _mock_post(*a, **kw):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise _make_mock_http_error(429)
            # Return a valid response body
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({
                "choices": [{"message": {"content": '{"action": "WAIT"}'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            }).encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            return mock_resp

        with patch.object(client, "_determine_endpoint", return_value="https://fake.endpoint"):
            with patch("urllib.request.urlopen", side_effect=_mock_post):
                with patch("time.sleep"):
                    text, tokens = client._dispatch_http_request_with_tokens("prompt")

        assert '{"action": "WAIT"}' in text
        assert call_count == 2


# ─── allow_model_fallback=False ───────────────────────────────────────────────

class TestNoModelFallback:
    def _live_client_no_fb(self) -> GenericLLMClient:
        client = _offline_client(
            provider="gemini",
            model="gemini-3.8-flash",
            api_key="fake-key-123456",
            allow_model_fallback=False,
        )
        client._force_live = True
        return client

    def test_503_raises_immediately_without_fallback(self):
        client = self._live_client_no_fb()

        def _mock_post(*a, **kw):
            raise _make_mock_http_error(503, "overloaded")

        with patch.object(client, "_determine_endpoint", return_value="https://fake.endpoint"):
            with patch("urllib.request.urlopen", side_effect=_mock_post):
                with pytest.raises(RuntimeError, match="503"):
                    client._dispatch_http_request_with_tokens("prompt")

        # Confirm no fallback occurred
        assert client.fallback_triggered is False
        assert client.model_name == "gemini-3.8-flash"

    def test_404_raises_immediately_without_fallback(self):
        client = self._live_client_no_fb()

        def _mock_post(*a, **kw):
            raise _make_mock_http_error(404, "not found")

        with patch.object(client, "_determine_endpoint", return_value="https://fake.endpoint"):
            with patch("urllib.request.urlopen", side_effect=_mock_post):
                with pytest.raises(RuntimeError, match="404"):
                    client._dispatch_http_request_with_tokens("prompt")

    def test_allow_fallback_true_tries_next_model_on_503(self):
        """Baseline: allow_model_fallback=True should try next model once retries on first model are exhausted."""
        client = _offline_client(
            provider="gemini",
            model="gemini-3.8-flash",
            api_key="fake-key-123456",
            allow_model_fallback=True,
            max_retries=0,  # 0 retries on first model so it falls back immediately on 503
            request_delay_seconds=0,
        )
        client._force_live = True

        call_count = 0
        def _mock_post(*a, **kw):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise _make_mock_http_error(503)
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({
                "choices": [{"message": {"content": "{}"}}],
                "usage": {}
            }).encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            return mock_resp

        with patch.object(client, "_determine_endpoint", return_value="https://fake.endpoint"):
            with patch("urllib.request.urlopen", side_effect=_mock_post):
                text, _ = client._dispatch_http_request_with_tokens("prompt")

        assert client.fallback_triggered is True
        assert call_count == 2



# ─── ControlledLiveBenchmarkRunner: offline ────────────────────────────────────

class TestControlledLiveBenchmarkRunnerOffline:
    """Tests that run entirely offline (no network) using mock investigation results."""

    def test_infra_failure_classification_429(self):
        err = RuntimeError("HTTP 429 quota exhausted")
        label = ControlledLiveBenchmarkRunner._classify_infra_failure(err, "")
        assert label == ControlledLiveBenchmarkRunner._INFRA_HTTP_429

    def test_infra_failure_classification_timeout(self):
        err = TimeoutError("urlopen error: timed out")
        label = ControlledLiveBenchmarkRunner._classify_infra_failure(err, "")
        assert label == ControlledLiveBenchmarkRunner._INFRA_TIMEOUT

    def test_infra_failure_classification_5xx(self):
        err = RuntimeError("LLM API HTTP error 503: overloaded")
        label = ControlledLiveBenchmarkRunner._classify_infra_failure(err, "")
        assert label == ControlledLiveBenchmarkRunner._INFRA_HTTP_5XX

    def test_infra_failure_classification_no_model(self):
        err = RuntimeError("LLM API HTTP error 404: model not found")
        label = ControlledLiveBenchmarkRunner._classify_infra_failure(err, "")
        assert label == ControlledLiveBenchmarkRunner._INFRA_NO_MODEL

    def test_infra_failure_classification_other(self):
        err = RuntimeError("some unknown error")
        label = ControlledLiveBenchmarkRunner._classify_infra_failure(err, "")
        assert label == ControlledLiveBenchmarkRunner._INFRA_OTHER

    def test_default_client_has_no_fallback(self):
        runner = ControlledLiveBenchmarkRunner(
            llm_client=_offline_client(allow_model_fallback=False)
        )
        assert runner.llm_client.allow_model_fallback is False

    def test_run_controlled_benchmark_offline_complete(self, tmp_path):
        """Full offline run: all 23 scenarios should COMPLETE and benchmark_status=COMPLETE."""
        # Import here to avoid circular import issues at module level
        from neofinesse.generator.config import GeneratorConfig
        from neofinesse.generator.exporter import DataExporter
        from neofinesse.generator.synthetic import FinancialDataGenerator
        from neofinesse.ingestion.pipeline import IngestionPipeline

        data_dir = tmp_path / "data"
        gt_dir = tmp_path / "gt"
        config = GeneratorConfig(
            seed=42,
            num_orders=80,
            num_payments=80,
            num_settlements=8,
            num_refunds=10,
            num_disputes=5,
            num_adjustments=5,
            num_transfers=3,
            output_dir=str(data_dir),
            ground_truth_dir=str(gt_dir),
        )
        world = FinancialDataGenerator(config).generate()
        exporter = DataExporter(world, config)
        export_meta = exporter.export_all()

        pipeline = IngestionPipeline(data_dir=str(data_dir))
        dataset = pipeline.run()
        gt_path = export_meta["ground_truth_path"]

        # Offline client (no API key → mock)
        client = _offline_client(allow_model_fallback=False, request_delay_seconds=0)
        runner = ControlledLiveBenchmarkRunner(llm_client=client)
        summary = runner.run_controlled_benchmark(
            dataset,
            gt_path,
            export_dir=str(tmp_path / "controlled"),
        )

        assert summary["total_scenarios"] == 23
        assert summary["completed_scenarios"] == 23
        assert summary["infrastructure_failures"] == 0
        assert summary["completion_rate_pct"] == 100.0
        assert summary["infrastructure_failure_rate_pct"] == 0.0
        assert summary["benchmark_status"] == "COMPLETE"
        assert summary["benchmark_mode"] == "live_controlled"
        assert summary["allow_model_fallback"] is False
        assert summary["reasoning_decision_accuracy_pct"] is not None

    def test_run_controlled_benchmark_infra_failures_give_incomplete(self, tmp_path):
        """If even one scenario raises an infra exception, benchmark_status must be INCOMPLETE."""
        from neofinesse.generator.config import GeneratorConfig
        from neofinesse.generator.exporter import DataExporter
        from neofinesse.generator.synthetic import FinancialDataGenerator
        from neofinesse.ingestion.pipeline import IngestionPipeline

        data_dir = tmp_path / "data2"
        gt_dir = tmp_path / "gt2"
        config = GeneratorConfig(
            seed=42,
            num_orders=80,
            num_payments=80,
            num_settlements=8,
            num_refunds=10,
            num_disputes=5,
            num_adjustments=5,
            num_transfers=3,
            output_dir=str(data_dir),
            ground_truth_dir=str(gt_dir),
        )
        world = FinancialDataGenerator(config).generate()
        exporter = DataExporter(world, config)
        export_meta = exporter.export_all()

        pipeline = IngestionPipeline(data_dir=str(data_dir))
        dataset = pipeline.run()
        gt_path = export_meta["ground_truth_path"]

        client = _offline_client(allow_model_fallback=False, request_delay_seconds=0)
        runner = ControlledLiveBenchmarkRunner(llm_client=client)

        call_count = [0]
        original_investigate = None

        from neofinesse.agentic_investigation.controller import AgenticInvestigationController

        original_investigate = AgenticInvestigationController.investigate

        def _patched_investigate(self_ctrl, *a, **kw):
            call_count[0] += 1
            if call_count[0] == 1:
                raise TimeoutError("simulated network timeout")
            return original_investigate(self_ctrl, *a, **kw)

        with patch.object(AgenticInvestigationController, "investigate", _patched_investigate):
            summary = runner.run_controlled_benchmark(
                dataset,
                gt_path,
                export_dir=str(tmp_path / "controlled_incomplete"),
            )

        assert summary["benchmark_status"] == "INCOMPLETE"
        assert summary["infrastructure_failures"] == 1
        assert summary["completed_scenarios"] == 22
        assert summary["infra_failure_breakdown"][ControlledLiveBenchmarkRunner._INFRA_TIMEOUT] == 1

    def test_exports_are_written(self, tmp_path):
        from neofinesse.generator.config import GeneratorConfig
        from neofinesse.generator.exporter import DataExporter
        from neofinesse.generator.synthetic import FinancialDataGenerator
        from neofinesse.ingestion.pipeline import IngestionPipeline

        data_dir = tmp_path / "data3"
        gt_dir = tmp_path / "gt3"
        config = GeneratorConfig(
            seed=42,
            num_orders=80,
            num_payments=80,
            num_settlements=8,
            num_refunds=10,
            num_disputes=5,
            num_adjustments=5,
            num_transfers=3,
            output_dir=str(data_dir),
            ground_truth_dir=str(gt_dir),
        )
        world = FinancialDataGenerator(config).generate()
        exporter = DataExporter(world, config)
        export_meta = exporter.export_all()

        pipeline = IngestionPipeline(data_dir=str(data_dir))
        dataset = pipeline.run()
        gt_path = export_meta["ground_truth_path"]

        client = _offline_client(allow_model_fallback=False, request_delay_seconds=0)
        runner = ControlledLiveBenchmarkRunner(llm_client=client)
        export_dir = tmp_path / "export_check"
        runner.run_controlled_benchmark(
            dataset,
            gt_path,
            export_dir=str(export_dir),
        )

        assert (export_dir / "results.json").exists()
        assert (export_dir / "results.csv").exists()
        assert (export_dir / "scenario_audit.csv").exists()
        assert (export_dir / "README.md").exists()


# ─── CSV / README helper functions ────────────────────────────────────────────

class TestControlledExportHelpers:
    def _make_completed_row(self, idx: int) -> Dict[str, Any]:
        return {
            "scenario_id": f"AG-{idx:03d}",
            "case_id": f"CASE-{idx}",
            "settlement_id": f"SETL-{idx}",
            "category": "TIMING",
            "ground_truth": "RESOLVED",
            "execution_status": "COMPLETED",
            "infra_failure_type": "",
            "infra_failure_detail": "",
            "correct": True,
            "final_decision": "RESOLVED",
            "rounds": 2,
            "tool_calls": 3,
            "reason_for_failure": "NONE",
            "primary_failure_category": "NONE",
            "false_closure": False,
            "false_escalation": False,
            "honest_exception": False,
            "llm_latency_ms": 500.0,
            "total_latency_ms": 600.0,
            "total_tokens": 200,
            "retries_this_scenario": 0,
            "429_this_scenario": 0,
            "provider": "mock",
            "requested_model": "mock-model",
            "effective_model": "mock-model",
            "allow_model_fallback": False,
            "request_delay_seconds": 0,
            "max_retries": 3,
        }

    def test_write_controlled_csv(self, tmp_path):
        rows = [self._make_completed_row(i) for i in range(3)]
        out = tmp_path / "test.csv"
        _write_controlled_csv(rows, out)
        assert out.exists()
        content = out.read_text()
        assert "scenario_id" in content
        assert "AG-000" in content

    def test_write_controlled_csv_empty(self, tmp_path):
        out = tmp_path / "empty.csv"
        _write_controlled_csv([], out)
        assert not out.exists()  # empty → file not created

    def test_write_controlled_audit_csv(self, tmp_path):
        rows = [self._make_completed_row(i) for i in range(2)]
        out = tmp_path / "audit.csv"
        _write_controlled_audit_csv(rows, out)
        assert out.exists()
        content = out.read_text()
        assert "ground_truth" in content

    def test_write_controlled_audit_csv_empty(self, tmp_path):
        out = tmp_path / "empty_audit.csv"
        _write_controlled_audit_csv([], out)
        assert not out.exists()

    def test_write_controlled_readme_complete(self, tmp_path):
        summary = {
            "benchmark_status": "COMPLETE",
            "provider": "gemini",
            "requested_model": "gemini-3.8-flash",
            "effective_model": "gemini-3.8-flash",
            "allow_model_fallback": False,
            "request_delay_seconds": 4.0,
            "max_retries": 3,
            "is_live_remote": True,
            "total_scenarios": 23,
            "completed_scenarios": 23,
            "completion_rate_pct": 100.0,
            "infrastructure_failures": 0,
            "infrastructure_failure_rate_pct": 0.0,
            "total_429_retries": 2,
            "reasoning_decision_accuracy_pct": 78.3,
            "correct_over_completed": 18,
            "false_closure_rate_pct": 0.0,
            "false_escalation_rate_pct": 14.3,
            "honest_exception_rate_pct": 85.7,
            "avg_llm_latency_ms": 1200.0,
            "avg_total_latency_ms": 1350.0,
            "avg_tokens_used": 450.0,
            "wall_time_seconds": 320.5,
        }
        out = tmp_path / "README.md"
        _write_controlled_readme(summary, out)
        content = out.read_text()
        assert "COMPLETE" in content
        assert "gemini-3.8-flash" in content
        assert "78.3" in content
        assert "Infrastructure Failures" in content

    def test_write_controlled_readme_incomplete(self, tmp_path):
        summary = {
            "benchmark_status": "INCOMPLETE",
            "provider": "gemini",
            "requested_model": "gemini-3.8-flash",
            "effective_model": "gemini-3.8-flash",
            "allow_model_fallback": False,
            "request_delay_seconds": 4.0,
            "max_retries": 3,
            "is_live_remote": True,
            "total_scenarios": 23,
            "completed_scenarios": 20,
            "completion_rate_pct": 87.0,
            "infrastructure_failures": 3,
            "infrastructure_failure_rate_pct": 13.0,
            "total_429_retries": 9,
            "reasoning_decision_accuracy_pct": None,
            "correct_over_completed": 0,
            "false_closure_rate_pct": None,
            "false_escalation_rate_pct": None,
            "honest_exception_rate_pct": None,
            "avg_llm_latency_ms": None,
            "avg_total_latency_ms": None,
            "avg_tokens_used": None,
            "wall_time_seconds": 180.0,
        }
        out = tmp_path / "README_incomplete.md"
        _write_controlled_readme(summary, out)
        content = out.read_text(encoding="utf-8")
        assert "INCOMPLETE" in content
        assert "N/A (no scenarios completed)" in content
