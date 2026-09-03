import io
import json
import os
from pathlib import Path
import unittest.mock as mock
import urllib.error
import pytest

from neofinesse.agentic_investigation.controller import AgenticInvestigationController
from neofinesse.agentic_investigation.live_benchmark import LiveAgenticBenchmarkRunner
from neofinesse.agentic_investigation.llm_client import (
    BaseLLMClient,
    GenericLLMClient,
    LiveMockMode,
    MockLLMClient,
)
from neofinesse.agentic_investigation.models import AgentInvestigationStatus, InvestigationBudget
from neofinesse.agentic_investigation.parser import AgentResponseParser
from neofinesse.agentic_investigation.planner import LiveAgentPlanner
from neofinesse.agentic_investigation.state import InvestigationState
from neofinesse.agentic_investigation.trace import InvestigationTraceFormatter
from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestionPipeline
from neofinesse.investigation.models import InvestigationStatus


@pytest.fixture(scope="module")
def live_test_env(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("live_env")
    data_dir = tmp / "data"
    gt_dir = tmp / "gt"

    config = GeneratorConfig(
        seed=42,
        output_dir=str(data_dir),
        ground_truth_dir=str(gt_dir),
    )
    world = FinancialDataGenerator(config).generate()
    exporter = DataExporter(world, config)
    res = exporter.export_all()

    pipeline = IngestionPipeline(data_dir=str(data_dir))
    dataset = pipeline.run()

    return {
        "dataset": dataset,
        "gt_path": res["ground_truth_path"],
        "exp_dir": str(tmp / "experiments"),
    }


def test_base_llm_client_interface():
    """Verifies BaseLLMClient interface and metadata generation wrapper."""
    class SimpleClient(BaseLLMClient):
        provider_name = "test-provider"
        model_name = "test-model-1"

        def generate(self, prompt: str, system_prompt: str = None) -> str:
            return '{"status": "ESCALATE", "reasoning": "Simple test response"}'

    client = SimpleClient()
    resp = client.generate_with_metadata("test prompt")
    assert resp.text == '{"status": "ESCALATE", "reasoning": "Simple test response"}'
    assert resp.latency_ms >= 0.0
    assert resp.provider == "test-provider"
    assert resp.model == "test-model-1"
    assert resp.error is None


def test_mock_llm_client_modes():
    """Verifies MockLLMClient execution modes for tests and benchmark."""
    normal_client = MockLLMClient(mode=LiveMockMode.NORMAL)
    res = normal_client.generate("Please investigate")
    assert '"status": "SUFFICIENT"' in res

    timeout_client = MockLLMClient(mode=LiveMockMode.TIMEOUT)
    with pytest.raises(TimeoutError):
        timeout_client.generate("Test timeout")

    broken_client = MockLLMClient(mode=LiveMockMode.MALFORMED_JSON)
    assert "BROKEN_JSON" in broken_client.generate("Test malformed")

    empty_client = MockLLMClient(mode=LiveMockMode.EMPTY_RESPONSE)
    assert empty_client.generate("Test empty") == ""


def test_generic_llm_client_env_config_and_secret_masking(monkeypatch):
    """Verifies GenericLLMClient reads exclusively from env vars and strictly masks credentials."""
    secret_key = "sk-live-secret-test-key-99998888"
    monkeypatch.setenv("NEOFINESSE_LLM_PROVIDER", "openai")
    monkeypatch.setenv("NEOFINESSE_LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("NEOFINESSE_LLM_API_KEY", secret_key)
    monkeypatch.setenv("NEOFINESSE_LLM_BASE_URL", "https://api.openai.com/v1")

    client = GenericLLMClient()
    assert client.provider_name == "openai"
    assert client.model_name == "gpt-4o-mini"
    assert client.base_url == "https://api.openai.com/v1"
    assert client.is_live_configured is True

    # Security: Ensure secret key is NEVER printed in string representation
    client_repr = repr(client)
    assert secret_key not in client_repr
    assert "sk-l...88" in client_repr

    # Without API key, falls back gracefully to mock
    monkeypatch.delenv("NEOFINESSE_LLM_API_KEY")
    client_no_key = GenericLLMClient()
    assert client_no_key.is_live_configured is False
    # Test generation does not fail or throw network error; falls back safely
    resp = client_no_key.generate("Test fallback")
    assert '"status"' in resp


def test_generic_llm_client_http_dispatch(monkeypatch):
    """Verifies GenericLLMClient mock HTTP request handling and token counting."""
    fake_response = {
        "choices": [{"message": {"content": '{"status": "ESCALATE", "reasoning": "Mocked API answer"}'}}],
        "usage": {"prompt_tokens": 120, "completion_tokens": 45, "total_tokens": 165},
    }
    fake_body = json.dumps(fake_response).encode("utf-8")

    class FakeHTTPResponse:
        def read(self):
            return fake_body
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    with mock.patch("urllib.request.urlopen", return_value=FakeHTTPResponse()):
        client = GenericLLMClient(provider="openai", model="gpt-4o", api_key="sk-test-mock-key", force_live=True)
        resp = client.generate_with_metadata("Explain this deficit")

        assert "Mocked API answer" in resp.text
        assert resp.total_tokens == 165
        assert resp.prompt_tokens == 120
        assert resp.completion_tokens == 45
        assert resp.error is None


def test_generic_llm_client_endpoints(monkeypatch):
    """Verifies endpoint determination for OpenAI, Groq, and Gemini."""
    c_openai = GenericLLMClient(provider="openai", api_key="sk-1")
    assert "api.openai.com" in c_openai._determine_endpoint()

    c_groq = GenericLLMClient(provider="groq", api_key="sk-2")
    assert "api.groq.com" in c_groq._determine_endpoint()

    c_gemini = GenericLLMClient(provider="gemini", api_key="sk-3")
    assert "generativelanguage.googleapis.com" in c_gemini._determine_endpoint()

    c_custom = GenericLLMClient(provider="local", api_key="sk-4", base_url="http://localhost:11434/v1")
    assert c_custom._determine_endpoint() == "http://localhost:11434/v1/chat/completions"


def test_model_name_normalization_and_provider_autodetection():
    """Verifies Gemini 3.7/3.8 Flash, Groq OSS 20B/120B normalization and provider auto-detection."""
    # 1. Gemini 3.7 Flash & 3.8 Flash variations
    c_g37 = GenericLLMClient(provider="gemini", model="gemini 3.7 flah", api_key="dummy")
    assert c_g37.model_name == "gemini-3.7-flash"
    assert c_g37.provider_name == "gemini"

    c_g38 = GenericLLMClient(provider="gemini", model="3.8 flash", api_key="dummy")
    assert c_g38.model_name == "gemini-3.8-flash"

    # Auto-detection from model name without explicit provider
    c_auto_gemini = GenericLLMClient(model="gemini-3.7-flash", api_key="dummy")
    assert c_auto_gemini.provider_name == "gemini"
    assert "generativelanguage.googleapis.com" in c_auto_gemini._determine_endpoint()

    # 2. Groq opennaioss-20b & 120b variations
    c_groq_20b = GenericLLMClient(provider="groq", model="opennaioss-20b", api_key="dummy")
    assert c_groq_20b.model_name == "openai/gpt-oss-20b"
    assert c_groq_20b.provider_name == "groq"

    c_groq_120b = GenericLLMClient(provider="groq", model="120b", api_key="dummy")
    assert c_groq_120b.model_name == "openai/gpt-oss-120b"

    c_groq_raw = GenericLLMClient(model="openaioss-20b", api_key="dummy")
    assert c_groq_raw.provider_name == "groq"
    assert c_groq_raw.model_name == "openai/gpt-oss-20b"
    assert "api.groq.com" in c_groq_raw._determine_endpoint()

    # 3. Arbitrary/custom model preservation
    c_custom = GenericLLMClient(provider="groq", model="deepseek-r1-distill-llama-70b", api_key="dummy")
    assert c_custom.model_name == "deepseek-r1-distill-llama-70b"


def test_parser_alias_normalization():
    """Verifies parser handles LLM aliases like evidence_gaps, tool_requests, reasoning_summary."""
    raw_json = json.dumps(
        {
            "evidence_gaps": ["Missing bank statement for UTR"],
            "tool_requests": [
                {
                    "request_id": "REQ-1",
                    "tool": "verify_membership",
                    "arguments": {"event_id": "ADJ-1", "settlement_id": "SET-1"},
                    "reason": "Verify adjustment",
                }
            ],
            "reasoning_summary": "Need additional evidence to confirm deduction.",
        }
    )

    resp, err = AgentResponseParser.parse_response(raw_json)
    assert err is None
    assert resp is not None
    assert resp.status == AgentInvestigationStatus.NEEDS_EVIDENCE
    assert resp.missing_evidence == ["Missing bank statement for UTR"]
    assert len(resp.investigation_requests) == 1
    assert resp.investigation_requests[0].tool == "verify_membership"
    assert resp.reasoning == "Need additional evidence to confirm deduction."


def test_live_agent_planner_controller_integration(live_test_env):
    """Verifies LiveAgentPlanner and controller tracking of multi-component latency breakdown."""
    dataset = live_test_env["dataset"]
    mock_client = MockLLMClient(mode=LiveMockMode.NORMAL)

    controller = AgenticInvestigationController(
        planner=LiveAgentPlanner(llm_client=mock_client),
    )

    target_setl = next(s for s in dataset.settlements if "scen_001" in s.id)
    res = controller.investigate(
        case_id="CASE-LIVE-TEST",
        settlement_id=target_setl.id,
        target_variance=-100000,
        dataset=dataset,
    )

    assert res.final_status in (InvestigationStatus.RESOLVED, InvestigationStatus.ESCALATE)
    assert res.llm_latency_ms >= 0.0
    assert res.tool_latency_ms >= 0.0
    assert res.orchestration_latency_ms >= 0.0
    assert res.investigation_latency_ms >= (res.llm_latency_ms + res.tool_latency_ms)
    assert res.llm_provider == "mock"
    assert res.llm_model == "mock-agent-v1"


def test_trace_formatter_latency_accounting(live_test_env):
    """Verifies trace formatting includes latency & cost accounting without exposing secrets."""
    dataset = live_test_env["dataset"]
    mock_client = MockLLMClient(mode=LiveMockMode.NORMAL)

    controller = AgenticInvestigationController(
        planner=LiveAgentPlanner(llm_client=mock_client),
    )

    target_setl = next(s for s in dataset.settlements if "scen_001" in s.id)
    res = controller.investigate(
        case_id="CASE-LIVE-TRACE-TEST",
        settlement_id=target_setl.id,
        target_variance=-100000,
        dataset=dataset,
    )

    state = InvestigationState.model_validate(res.state_snapshot)
    trace = InvestigationTraceFormatter.format_trace(state=state, result=res)

    assert "[OPERATIONAL LATENCY & COST ACCOUNTING]" in trace
    assert "LLM Investigation Time:" in trace
    assert "Tool Execution Time:" in trace
    assert "Local Orchestration Time:" in trace
    assert "End-to-End Total Time:" in trace
    assert "sk-" not in trace
    assert "Bearer" not in trace


def test_live_benchmark_runner(live_test_env):
    """Verifies LiveAgenticBenchmarkRunner executes 23 scenarios and exports strictly to experiments/phase7/live/."""
    dataset = live_test_env["dataset"]
    gt_path = live_test_env["gt_path"]
    exp_dir = live_test_env["exp_dir"]

    live_dir = Path(exp_dir) / "live"
    runner = LiveAgenticBenchmarkRunner()
    summary = runner.run_live_benchmark(dataset=dataset, ground_truth_path=gt_path, export_dir=str(live_dir))

    assert summary["total_scenarios_evaluated"] == 23
    assert summary["correct_terminal_decision_rate_pct"] > 0.0
    assert (live_dir / "results.json").exists()
    assert (live_dir / "results.csv").exists()


def test_dotenv_loading_into_generic_client(tmp_path, monkeypatch):
    """Verifies that key-values in .env are picked up by GenericLLMClient."""
    from neofinesse.agentic_investigation.llm_client import _load_dotenv_if_present

    env_file = tmp_path / ".env"
    env_file.write_text(
        "NEOFINESSE_LLM_TEST_VAR=test_val_123\n"
        "GEMINI_API_KEY=AIzaSy_fake_test_key\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("NEOFINESSE_LLM_TEST_VAR", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    _load_dotenv_if_present(str(env_file))

    assert os.getenv("NEOFINESSE_LLM_TEST_VAR") == "test_val_123"
    assert os.getenv("GEMINI_API_KEY") == "AIzaSy_fake_test_key"
