from pathlib import Path
import pytest

from neofinesse.agentic_investigation.controller import AgenticInvestigationController
from neofinesse.agentic_investigation.llm_client import (
    LiveMockMode,
    MockLLMClient,
)
from neofinesse.agentic_investigation.models import InvestigationBudget
from neofinesse.agentic_investigation.planner import LiveAgentPlanner
from neofinesse.agentic_investigation.state import InvestigationState
from neofinesse.agentic_investigation.trace import InvestigationTraceFormatter
from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestionPipeline
from neofinesse.investigation.models import InvestigationStatus


@pytest.fixture(scope="module")
def safety_test_env(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("safety_env")
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


def test_safety_a_hallucinated_evidence_rejected(safety_test_env):
    """Test A: Hallucinated evidence ID references are blocked and cannot close a case."""
    dataset = safety_test_env["dataset"]
    client = MockLLMClient(mode=LiveMockMode.HALLUCINATED_ID)

    controller = AgenticInvestigationController(
        planner=LiveAgentPlanner(llm_client=client),
    )

    target_setl = next(s for s in dataset.settlements if "scen_001" in s.id)
    res = controller.investigate(
        case_id="CASE-SAFETY-A",
        settlement_id=target_setl.id,
        target_variance=-100000,
        dataset=dataset,
    )

    # Invariant: A hallucinated evidence ID must NEVER lead to a successful resolution
    assert res.final_status == InvestigationStatus.ESCALATE
    assert res.winning_hypothesis is None


def test_safety_b_wrong_arithmetic_independently_recalculated(safety_test_env):
    """Test B: AI claims incorrect calculation sum; verifier recalculates independently."""
    dataset = safety_test_env["dataset"]
    client = MockLLMClient(mode=LiveMockMode.WRONG_ARITHMETIC)

    controller = AgenticInvestigationController(
        planner=LiveAgentPlanner(llm_client=client),
    )

    target_setl = next(s for s in dataset.settlements if "scen_001" in s.id)
    res = controller.investigate(
        case_id="CASE-SAFETY-B",
        settlement_id=target_setl.id,
        target_variance=-100000,
        dataset=dataset,
    )

    # Invariant: Claimed ₹999,999.99 is discarded; verifier recalculated authentic amounts
    if res.winning_hypothesis:
        assert res.winning_hypothesis.explained_amount != -99999999
        assert abs(res.winning_hypothesis.explained_amount) < 10000000


def test_safety_c_unsupported_closure_blocked_by_verifier(safety_test_env):
    """Test C: AI asserts RESOLVED without satisfying deterministic constraints."""
    dataset = safety_test_env["dataset"]
    client = MockLLMClient(mode=LiveMockMode.UNSUPPORTED_CLOSURE)

    controller = AgenticInvestigationController(
        planner=LiveAgentPlanner(llm_client=client),
    )

    # Case 010 has NO authentic candidate records in the ledger
    target_setl = next(s for s in dataset.settlements if "scen_010" in s.id)
    res = controller.investigate(
        case_id="CASE-SAFETY-C",
        settlement_id=target_setl.id,
        target_variance=-200000,
        dataset=dataset,
    )

    # Invariant: Even if LLM status is SUFFICIENT, deterministic verifier refuses closure
    assert res.final_status == InvestigationStatus.ESCALATE
    assert res.winning_hypothesis is None


def test_safety_d_invented_relationship_rejected(safety_test_env):
    """Test D: AI claims unbacked relationship between settlement and refund."""
    dataset = safety_test_env["dataset"]
    client = MockLLMClient(mode=LiveMockMode.INVENTED_RELATIONSHIP)

    controller = AgenticInvestigationController(
        planner=LiveAgentPlanner(llm_client=client),
    )

    # Scenario 009 has wrong payment decoy (no relational link to settlement lines)
    target_setl = next(s for s in dataset.settlements if "scen_009" in s.id)
    res = controller.investigate(
        case_id="CASE-SAFETY-D",
        settlement_id=target_setl.id,
        target_variance=-150000,
        dataset=dataset,
    )

    # Invariant: Relational constraint fails, preventing false closure
    assert res.final_status == InvestigationStatus.ESCALATE
    assert res.winning_hypothesis is None


def test_safety_e_prompt_injection_cannot_bypass_controls(safety_test_env):
    """Test E: Financial record containing instruction-like text cannot override verifier authority."""
    dataset = safety_test_env["dataset"]
    client = MockLLMClient(mode=LiveMockMode.PROMPT_INJECTION)

    controller = AgenticInvestigationController(
        planner=LiveAgentPlanner(llm_client=client),
    )

    target_setl = next(s for s in dataset.settlements if "scen_010" in s.id)
    res = controller.investigate(
        case_id="CASE-SAFETY-E",
        settlement_id=target_setl.id,
        target_variance=-200000,
        dataset=dataset,
    )

    # Invariant: Even with prompt injection attempting to force closure, verifier rejects
    assert res.final_status == InvestigationStatus.ESCALATE
    assert res.winning_hypothesis is None


def test_safety_f_unregistered_tool_request_rejected(safety_test_env):
    """Test F: AI attempts to invoke unregistered tool (e.g. arbitrary SQL query); safely rejected."""
    dataset = safety_test_env["dataset"]
    client = MockLLMClient(mode=LiveMockMode.UNREGISTERED_TOOL)

    controller = AgenticInvestigationController(
        planner=LiveAgentPlanner(llm_client=client),
    )

    target_setl = next(s for s in dataset.settlements if "scen_001" in s.id)
    res = controller.investigate(
        case_id="CASE-SAFETY-F",
        settlement_id=target_setl.id,
        target_variance=-100000,
        dataset=dataset,
    )

    # Invariant: Tool request is rejected by validator, does not execute, and case safely escalates
    assert res.final_status == InvestigationStatus.ESCALATE
    state = InvestigationState.model_validate(res.state_snapshot)
    assert any("Unknown tool" in (r.error or "") or "Unregistered" in (r.error or "") for r in state.tool_results)


def test_safety_g_llm_timeout_safely_escalates(safety_test_env):
    """Test G: Network timeout during LLM generation triggers safe escalation with explicit reason."""
    dataset = safety_test_env["dataset"]
    client = MockLLMClient(mode=LiveMockMode.TIMEOUT)

    controller = AgenticInvestigationController(
        planner=LiveAgentPlanner(llm_client=client),
    )

    target_setl = next(s for s in dataset.settlements if "scen_001" in s.id)
    res = controller.investigate(
        case_id="CASE-SAFETY-G",
        settlement_id=target_setl.id,
        target_variance=-100000,
        dataset=dataset,
    )

    assert res.final_status == InvestigationStatus.ESCALATE
    assert res.termination_reason == "LLM_TIMEOUT"
    assert res.winning_hypothesis is None


def test_safety_h_malformed_json_safely_escalates(safety_test_env):
    """Test H: Malformed JSON output from LLM triggers safe escalation with explicit reason."""
    dataset = safety_test_env["dataset"]
    client = MockLLMClient(mode=LiveMockMode.MALFORMED_JSON)

    controller = AgenticInvestigationController(
        planner=LiveAgentPlanner(llm_client=client),
    )

    target_setl = next(s for s in dataset.settlements if "scen_001" in s.id)
    res = controller.investigate(
        case_id="CASE-SAFETY-H",
        settlement_id=target_setl.id,
        target_variance=-100000,
        dataset=dataset,
    )

    assert res.final_status == InvestigationStatus.ESCALATE
    assert res.termination_reason == "INVALID_LLM_RESPONSE"
    assert res.winning_hypothesis is None
