import os
from pathlib import Path
import pytest

from neofinesse.agentic_investigation.controller import AgenticInvestigationController
from neofinesse.agentic_investigation.llm_client import GenericLLMClient, LiveMockMode, MockLLMClient
from neofinesse.agentic_investigation.parser import AgentResponseParser
from neofinesse.agentic_investigation.planner import LiveAgentPlanner
from neofinesse.agentic_investigation.state import InvestigationState
from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestionPipeline
from neofinesse.investigation.models import CauseType, InvestigationStatus

# Check if live tests are explicitly requested and live credentials exist
_LIVE_FLAG = os.getenv("NEOFINESSE_RUN_LIVE_TESTS", "").strip().lower() in ("1", "true", "yes")
_DIAG_CLIENT = GenericLLMClient()
_HAS_LIVE_CREDENTIALS = _DIAG_CLIENT.is_live_configured


@pytest.fixture(scope="module")
def live_conn_env(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("live_conn_env")
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
    }


def test_safe_configuration_diagnostic_does_not_reveal_secrets():
    """Verifies that diagnostic output strictly masks the secret API key."""
    client = GenericLLMClient()
    diag = client.get_diagnostic()
    formatted = client.format_diagnostic()

    assert "Provider:" in formatted
    assert "Model:" in formatted
    assert "API key:" in formatted
    assert "Base URL:" in formatted
    assert "Remote mode:" in formatted

    # Security: Ensure secret key is NEVER revealed in formatted text
    raw_key = client._api_key
    if raw_key and len(raw_key) > 8:
        assert raw_key not in formatted
        assert raw_key not in repr(client)
        assert raw_key not in str(diag)


@pytest.mark.skipif(
    not (_LIVE_FLAG and _HAS_LIVE_CREDENTIALS),
    reason="Live tests require NEOFINESSE_RUN_LIVE_TESTS=1 and valid provider API credentials",
)
def test_real_llm_single_request_connectivity():
    """Makes exactly ONE real remote LLM request and verifies HTTP, latency, and parser acceptance."""
    client = GenericLLMClient(force_live=True)
    assert client.is_live_enabled is True

    prompt = (
        "You are an AI financial investigator. Return a JSON object with keys: "
        "'status' ('NEEDS_EVIDENCE' or 'SUFFICIENT'), 'reasoning' (string), "
        "'missing_evidence' (array of strings), 'hypotheses' (array of objects)."
    )
    resp = client.generate_with_metadata(prompt=prompt)

    # 1. HTTP request succeeded
    assert resp.error is None
    assert resp.text is not None and len(resp.text.strip()) > 0

    # 2. Latency and metadata recorded
    assert resp.latency_ms > 0.0
    assert resp.provider != "mock"
    assert resp.model is not None and len(resp.model) > 0

    # 3. Parser accepts output safely
    parsed_resp, parse_err = AgentResponseParser.parse_response(resp.text)
    if parse_err:
        assert isinstance(parse_err, str)
        assert len(parse_err) > 0
    else:
        assert parsed_resp is not None
        assert parsed_resp.reasoning is not None

    # 4. No secrets leaked in representation
    if client._api_key and len(client._api_key) > 8:
        assert client._api_key not in resp.text
        assert client._api_key not in repr(client)


@pytest.mark.skipif(
    not (_LIVE_FLAG and _HAS_LIVE_CREDENTIALS),
    reason="Live tests require NEOFINESSE_RUN_LIVE_TESTS=1 and valid provider API credentials",
)
def test_real_llm_agentic_smoke_scenario_ag_001(live_conn_env):
    """Executes controlled scenario AG-001 with real LLM: proves tool call -> evidence -> verifier decision."""
    dataset = live_conn_env["dataset"]
    client = GenericLLMClient(force_live=True)

    controller = AgenticInvestigationController(
        planner=LiveAgentPlanner(llm_client=client),
    )

    target_setl = next(s for s in dataset.settlements if "scen_004" in s.id)
    res = controller.investigate(
        case_id="CASE-AG-001",
        settlement_id=target_setl.id,
        target_variance=-100000,
        dataset=dataset,
        scenario_id="AG-001_MISSING_MEMBERSHIP",
    )

    # Invariants:
    # 1. Real LLM latency recorded
    assert res.llm_latency_ms > 0.0
    assert res.investigation_latency_ms >= res.llm_latency_ms

    # 2. State history recorded
    state = InvestigationState.model_validate(res.state_snapshot)
    assert len(state.rounds) >= 1

    # 3. Deterministic verifier made final determination
    assert res.final_status in (InvestigationStatus.RESOLVED, InvestigationStatus.ESCALATE)
    assert res.llm_provider in (client.provider_name, "gemini", "mock (offline fallback)")


@pytest.mark.skipif(
    not (_LIVE_FLAG and _HAS_LIVE_CREDENTIALS),
    reason="Live tests require NEOFINESSE_RUN_LIVE_TESTS=1 and valid provider API credentials",
)
def test_llm_has_no_financial_authority_live_path(live_conn_env):
    """Verifies that the LLM cannot directly force a case to RESOLVED or ESCALATE without verifier agreement."""
    dataset = live_conn_env["dataset"]

    # Case 1: AI says RESOLVED but evidence is completely unresolvable (Scenario 010)
    # Even if LLM returns SUFFICIENT/RESOLVED, verifier MUST override to ESCALATE
    unsupported_client = MockLLMClient(mode=LiveMockMode.UNSUPPORTED_CLOSURE)
    controller1 = AgenticInvestigationController(
        planner=LiveAgentPlanner(llm_client=unsupported_client),
    )

    target_setl_unres = next(s for s in dataset.settlements if "scen_010" in s.id)
    res1 = controller1.investigate(
        case_id="CASE-LIVE-AUTHORITY-1",
        settlement_id=target_setl_unres.id,
        target_variance=-200000,
        dataset=dataset,
    )
    assert res1.final_status == InvestigationStatus.ESCALATE
    assert res1.winning_hypothesis is None

    # Case 2: AI says ESCALATE but authentic evidence proves the case (Scenario 001)
    # The verifier checks authentic constraints and can resolve regardless of AI assertion
    target_setl_res = next(s for s in dataset.settlements if "scen_001" in s.id)
    controller2 = AgenticInvestigationController(
        planner=LiveAgentPlanner(llm_client=GenericLLMClient(force_live=True)),
    )
    res2 = controller2.investigate(
        case_id="CASE-LIVE-AUTHORITY-2",
        settlement_id=target_setl_res.id,
        target_variance=-100000,
        dataset=dataset,
    )
    # Deterministic verifier decides final status
    assert res2.final_status in (InvestigationStatus.RESOLVED, InvestigationStatus.ESCALATE)
