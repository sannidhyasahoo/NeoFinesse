from pathlib import Path
import pytest

from neofinesse.agentic_investigation.benchmark import AgenticBenchmarkRunner
from neofinesse.agentic_investigation.controller import AgenticInvestigationController
from neofinesse.agentic_investigation.models import (
    AgentHypothesisProposal,
    AgentInvestigationStatus,
    AgentRoundResponse,
    InvestigationBudget,
    ToolRequest,
)
from neofinesse.agentic_investigation.planner import MockAgentPlanner
from neofinesse.agentic_investigation.state import InvestigationState
from neofinesse.agentic_investigation.tool_registry import ToolRegistry
from neofinesse.agentic_investigation.tool_validator import ToolRequestValidator
from neofinesse.agentic_investigation.tools import InvestigationTools
from neofinesse.agentic_investigation.validator import AgentResponseValidator
from neofinesse.ai_investigation.evidence_pack import EvidenceItem
from neofinesse.ai_investigation.llm_client import MockMode
from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestionPipeline
from neofinesse.investigation.models import CauseType, InvestigationStatus
from neofinesse.retrieval.base import InvestigationTaskCategory


@pytest.fixture(scope="module")
def agentic_test_env(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("phase7_env")
    data_dir = temp_dir / "data"
    gt_dir = temp_dir / "ground_truth"
    exp_dir = temp_dir / "experiments"

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

    return {
        "dataset": dataset,
        "gt_path": export_meta["ground_truth_path"],
        "exp_dir": str(exp_dir),
        "data_dir": str(data_dir),
    }


# ==========================================
# 1. State & Round Snapshot Tests
# ==========================================

def test_state_initialization_and_evidence_deduplication():
    state = InvestigationState(case_id="CASE-01", settlement_id="SET-01", target_variance=-100000, task_category="SETTLEMENT_RCA")
    item1 = EvidenceItem(
        evidence_id="EV-1", candidate_id="c1", entity_id="e1", entity_type="refund",
        amount_paise=100000, amount_inr=1000.0, net_financial_effect_paise=-100000, net_financial_effect_inr=-1000.0,
        relationship_path="path", source_id="SRC-1", source_file="f1.csv", source_row=1, source_hash="h1", record_hash="h2"
    )
    added = state.add_evidence([item1, item1])
    assert added == ["EV-1"]
    assert len(state.current_evidence) == 1
    assert len(state.evidence_history) == 1


def test_round_record_snapshot_preservation():
    state = InvestigationState(case_id="CASE-01", settlement_id="SET-01", target_variance=-100000, task_category="SETTLEMENT_RCA")
    rec = state.record_round_snapshot(
        round_number=1,
        agent_response=None,
        tool_requests=[],
        tool_results=[],
        verified_hypotheses=[],
        rejected_reasons=[],
    )
    assert rec.round_number == 1
    assert len(state.rounds) == 1


# ==========================================
# 2. Tool Execution & Registry Tests
# ==========================================

def test_tool_verify_membership(agentic_test_env):
    dataset = agentic_test_env["dataset"]
    registry = ToolRegistry()

    setl = dataset.settlements[0]
    target_lines = [l for l in dataset.settlement_lines if l.settlement_id == setl.id]
    member_id = target_lines[0].source_event_id

    # Test member
    req_member = ToolRequest(
        request_id="REQ-1",
        tool="verify_membership",
        arguments={"event_id": member_id, "settlement_id": setl.id},
        reason="Verify membership",
    )
    res_member = registry.execute_tool(req_member, dataset)
    assert res_member.success is True
    assert res_member.output["membership_status"] == "MEMBER"
    assert len(res_member.evidence_items) == 1

    # Test non-member
    req_non_member = ToolRequest(
        request_id="REQ-2",
        tool="verify_membership",
        arguments={"event_id": "fake_unrelated_event", "settlement_id": setl.id},
        reason="Verify non-membership",
    )
    res_non_member = registry.execute_tool(req_non_member, dataset)
    assert res_non_member.success is True
    assert res_non_member.output["membership_status"] == "NOT_MEMBER"


def test_tool_retrieve_upi_history(agentic_test_env):
    dataset = agentic_test_env["dataset"]
    registry = ToolRegistry()

    upi_event = dataset.upi_events[0]
    req = ToolRequest(
        request_id="REQ-UPI",
        tool="retrieve_upi_history",
        arguments={"upi_transaction_id": upi_event.upi_transaction_id},
        reason="Retrieve UPI history",
    )
    res = registry.execute_tool(req, dataset)
    assert res.success is True
    assert "transitions" in res.output
    assert len(res.evidence_items) == 1


def test_tool_retrieve_temporal_neighbors_bounded(agentic_test_env):
    dataset = agentic_test_env["dataset"]
    registry = ToolRegistry()

    req = ToolRequest(
        request_id="REQ-TEMP",
        tool="retrieve_temporal_neighbors",
        arguments={
            "entity_id": dataset.settlements[0].id,
            "reference_timestamp": "2026-08-20T12:00:00",
            "window_before_minutes": 60,
            "window_after_minutes": 60,
        },
        reason="Check temporal window",
    )
    res = registry.execute_tool(req, dataset)
    assert res.success is True
    assert "window_matches" in res.output


# ==========================================
# 3. Tool Request Validation Tests
# ==========================================

def test_tool_validator_rejects_unregistered_tool():
    registry = ToolRegistry()
    state = InvestigationState(case_id="C1", settlement_id="S1", target_variance=0, task_category="SETTLEMENT_RCA")
    budget = InvestigationBudget()

    req = ToolRequest(request_id="R1", tool="arbitrary_unregistered_tool", arguments={}, reason="test")
    is_valid, err = ToolRequestValidator.validate_request(req, registry, state, budget)
    assert is_valid is False
    assert "Unknown tool" in err


def test_tool_validator_rejects_missing_arguments():
    registry = ToolRegistry()
    state = InvestigationState(case_id="C1", settlement_id="S1", target_variance=0, task_category="SETTLEMENT_RCA")
    budget = InvestigationBudget()

    req = ToolRequest(request_id="R1", tool="verify_membership", arguments={"event_id": "e1"}, reason="Missing settlement_id")
    is_valid, err = ToolRequestValidator.validate_request(req, registry, state, budget)
    assert is_valid is False
    assert "Missing required argument" in err


def test_tool_validator_rejects_wildcards_and_sql():
    registry = ToolRegistry()
    state = InvestigationState(case_id="C1", settlement_id="S1", target_variance=0, task_category="SETTLEMENT_RCA")
    budget = InvestigationBudget()

    req_wildcard = ToolRequest(request_id="R1", tool="verify_membership", arguments={"event_id": "*", "settlement_id": "S1"}, reason="test")
    is_valid, err = ToolRequestValidator.validate_request(req_wildcard, registry, state, budget)
    assert is_valid is False
    assert "Wildcard" in err

    req_sql = ToolRequest(request_id="R2", tool="verify_membership", arguments={"event_id": "e1; DROP TABLE settlements;", "settlement_id": "S1"}, reason="test")
    is_valid2, err2 = ToolRequestValidator.validate_request(req_sql, registry, state, budget)
    assert is_valid2 is False
    assert "injection patterns rejected" in err2


def test_tool_validator_rejects_duplicate_and_budget_exhaustion():
    registry = ToolRegistry()
    state = InvestigationState(case_id="C1", settlement_id="S1", target_variance=0, task_category="SETTLEMENT_RCA")
    budget = InvestigationBudget(max_tool_calls=2)

    req1 = ToolRequest(request_id="R1", tool="verify_membership", arguments={"event_id": "e1", "settlement_id": "S1"}, reason="test")
    state.completed_requests.append(req1)

    # Duplicate check
    is_valid, err = ToolRequestValidator.validate_request(req1, registry, state, budget)
    assert is_valid is False
    assert "Duplicate tool call" in err

    # Budget exhaustion check
    req2 = ToolRequest(request_id="R2", tool="verify_membership", arguments={"event_id": "e2", "settlement_id": "S1"}, reason="test")
    state.completed_requests.append(req2)

    req3 = ToolRequest(request_id="R3", tool="verify_membership", arguments={"event_id": "e3", "settlement_id": "S1"}, reason="test")
    is_valid3, err3 = ToolRequestValidator.validate_request(req3, registry, state, budget)
    assert is_valid3 is False
    assert "Tool call budget exhausted" in err3


# ==========================================
# 4. AI Safety & Hallucination Tests
# ==========================================

def test_agent_validator_rejects_hallucinated_evidence_id():
    state = InvestigationState(case_id="C1", settlement_id="S1", target_variance=-100000, task_category="SETTLEMENT_RCA")
    resp = AgentRoundResponse(
        status=AgentInvestigationStatus.SUFFICIENT,
        hypotheses=[
            AgentHypothesisProposal(
                hypothesis_id="h1", cause_type=CauseType.REFUND, evidence_ids=["EV-9999"],
                claimed_explained_amount=-100000, reasoning="Hallucinated"
            )
        ],
        investigation_requests=[],
        reasoning="Test",
    )
    verified, rejections = AgentResponseValidator.validate_and_bridge_hypotheses(resp, state)
    assert len(verified) == 0
    assert len(rejections) == 1
    assert "EV-9999" in rejections[0]["reason"]


def test_unsupported_closure_blocked_by_phase5_verifier(agentic_test_env):
    dataset = agentic_test_env["dataset"]
    planner = MockAgentPlanner(mode=MockMode.UNSUPPORTED_CLOSURE)
    controller = AgenticInvestigationController(planner=planner)

    target_setl = next(s for s in dataset.settlements if "scen_008" in s.id)
    res = controller.investigate(
        case_id="CASE-008",
        settlement_id=target_setl.id,
        target_variance=400000,
        dataset=dataset,
    )
    assert res.final_status == InvestigationStatus.ESCALATE
    assert res.winning_hypothesis is None


# ==========================================
# 5. Agentic Scenarios (AG-001 - AG-008)
# ==========================================

def test_ag_001_missing_membership_resolved(agentic_test_env):
    """AG-001: Missing membership verified via verify_membership tool in round 2 -> composite resolution."""
    dataset = agentic_test_env["dataset"]
    controller = AgenticInvestigationController()

    target_setl = next(s for s in dataset.settlements if "scen_004" in s.id)
    res = controller.investigate(
        case_id="CASE-AG-001",
        settlement_id=target_setl.id,
        target_variance=-100000,
        dataset=dataset,
    )
    assert res.final_status == InvestigationStatus.RESOLVED
    assert res.total_rounds == 2
    assert res.total_tool_calls == 1
    assert res.winning_hypothesis is not None
    assert res.winning_hypothesis.cause_type == CauseType.COMPOSITE


def test_ag_002_wrong_membership_revised_and_escalated(agentic_test_env):
    """AG-002: Candidate adjustment confirmed NOT_MEMBER; earlier hypothesis revised and escalated."""
    dataset = agentic_test_env["dataset"]
    controller = AgenticInvestigationController()

    target_setl = next(s for s in dataset.settlements if "scen_002" in s.id)
    res = controller.investigate(
        case_id="CASE-AG-002",
        settlement_id=target_setl.id,
        target_variance=-250000,
        dataset=dataset,
    )
    assert res.final_status == InvestigationStatus.ESCALATE
    assert res.total_rounds == 2
    assert res.revisions_count >= 1
    assert res.winning_hypothesis is None


def test_ag_003_missing_upi_history_resolved(agentic_test_env):
    """AG-003: Failed UPI investigated via retrieve_upi_history tool -> debit + auto-reversal verified."""
    dataset = agentic_test_env["dataset"]
    controller = AgenticInvestigationController()

    res = controller.investigate(
        case_id="CASE-AG-003",
        settlement_id="N/A",
        target_variance=0,
        dataset=dataset,
        task_category=InvestigationTaskCategory.UPI_STATE_INVESTIGATION,
    )
    assert res.final_status == InvestigationStatus.RESOLVED
    assert res.total_rounds == 2
    assert res.total_tool_calls == 1


def test_ag_004_late_upi_success_resolved(agentic_test_env):
    """AG-004: Timeout UPI investigated via retrieve_upi_history tool -> late authorization callback verified."""
    dataset = agentic_test_env["dataset"]
    controller = AgenticInvestigationController()

    target_setl = next(s for s in dataset.settlements if "scen_005" in s.id)
    res = controller.investigate(
        case_id="CASE-AG-004",
        settlement_id=target_setl.id,
        target_variance=0,
        dataset=dataset,
        task_category=InvestigationTaskCategory.UPI_STATE_INVESTIGATION,
    )
    assert res.final_status == InvestigationStatus.RESOLVED
    assert res.total_rounds == 2


def test_ag_005_conflicting_refund_escalated(agentic_test_env):
    """AG-005: Matching refund inspected via retrieve_source_record -> confirmed FAILED -> escalated."""
    dataset = agentic_test_env["dataset"]
    controller = AgenticInvestigationController()

    target_setl = next(s for s in dataset.settlements if "scen_002" in s.id)
    res = controller.investigate(
        case_id="CASE-AG-005",
        settlement_id=target_setl.id,
        target_variance=-250000,
        dataset=dataset,
    )
    assert res.final_status == InvestigationStatus.ESCALATE
    assert res.total_rounds == 2


def test_ag_006_truly_unexplained_escalated(agentic_test_env):
    """AG-006: Unexplained variance investigated via retrieve_temporal_neighbors -> no records -> escalated."""
    dataset = agentic_test_env["dataset"]
    controller = AgenticInvestigationController()

    target_setl = next(s for s in dataset.settlements if "scen_010" in s.id)
    res = controller.investigate(
        case_id="CASE-AG-006",
        settlement_id=target_setl.id,
        target_variance=-1500000,
        dataset=dataset,
    )
    assert res.final_status == InvestigationStatus.ESCALATE
    assert res.total_rounds == 2


def test_ag_007_decoy_explosion_pruned_and_resolved(agentic_test_env):
    """AG-007: Multiple same-amount candidates pruned via verify_membership tool -> resolved."""
    dataset = agentic_test_env["dataset"]
    controller = AgenticInvestigationController()

    target_setl = next(s for s in dataset.settlements if "scen_002" in s.id)
    res = controller.investigate(
        case_id="CASE-AG-007",
        settlement_id=target_setl.id,
        target_variance=-250000,
        dataset=dataset,
    )
    assert res.final_status == InvestigationStatus.RESOLVED
    assert res.total_rounds == 2


def test_ag_008_multi_step_flagship_investigation(agentic_test_env):
    """AG-008: Flagship 3-round investigation: related evidence -> membership verification -> composite resolution."""
    dataset = agentic_test_env["dataset"]
    controller = AgenticInvestigationController()

    target_setl = next(s for s in dataset.settlements if "scen_004" in s.id)
    res = controller.investigate(
        case_id="CASE-AG-008",
        settlement_id=target_setl.id,
        target_variance=-100000,
        dataset=dataset,
    )
    assert res.final_status == InvestigationStatus.RESOLVED
    assert res.total_rounds == 3
    assert res.total_tool_calls == 2
    assert res.winning_hypothesis is not None
    assert res.winning_hypothesis.cause_type == CauseType.COMPOSITE


# ==========================================
# 6. Benchmark Scorecard & File Export Test
# ==========================================

def test_phase7_benchmark_scorecard_and_comparison(agentic_test_env):
    """Benchmark: 18-case evaluation (Phase 5 vs Phase 6 vs Phase 7 vs Oracle) produces 100% accuracy and 0% false closures."""
    dataset = agentic_test_env["dataset"]
    gt_path = agentic_test_env["gt_path"]
    exp_dir = agentic_test_env["exp_dir"]

    runner = AgenticBenchmarkRunner()
    scorecard = runner.run_benchmark(dataset, gt_path, export_dir=exp_dir)

    assert scorecard.total_scenarios_evaluated == 18
    assert scorecard.phase7_accuracy_pct == 100.0
    assert scorecard.phase7_false_closure_rate_pct == 0.0
    assert scorecard.honest_exception_rate_pct == 100.0
    assert scorecard.partial_attribution_accuracy_pct == 100.0
    assert scorecard.resolution_rate_pct == 100.0
    assert scorecard.avg_investigation_rounds > 1.0
    assert scorecard.avg_tool_calls > 0.0

    assert (Path(exp_dir) / "scenarios.json").exists()
    assert (Path(exp_dir) / "results.json").exists()
    assert (Path(exp_dir) / "results.csv").exists()
