from pathlib import Path
import pytest

from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestedDataset, IngestionPipeline
from neofinesse.models.ground_truth import CaseGroundTruth, ExpectedOutcome, GroundTruthCause, GroundTruthDecoy, ScenarioType
from neofinesse.retrieval.attribute import AttributeRetrievalStrategy
from neofinesse.retrieval.base import (
    EvidenceCandidate,
    InvestigationTaskCategory,
    RetrievalResult,
    RetrievalStrategy,
    TemporalRetrievalStatus,
)
from neofinesse.retrieval.benchmark import RetrievalBenchmarkRunner
from neofinesse.retrieval.direct_id import DirectIdRetrievalStrategy
from neofinesse.retrieval.evaluator import (
    RetrievalEvaluator,
    ScenarioEvaluationRow,
    get_scenario_task_category,
)
from neofinesse.retrieval.provenance import TypedProvenanceRetrievalStrategy
from neofinesse.retrieval.relationship import RelationshipAwareRetrievalStrategy
from neofinesse.retrieval.temporal import TemporalRelationshipRetrievalStrategy
from neofinesse.retrieval.upi_event import UPIEventRetrievalStrategy


@pytest.fixture(scope="module")
def retrieval_test_env(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("phase4_eval_env")
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
# 1. Evaluator Metric Semantics Tests
# ==========================================

def test_evaluator_zero_expected_causes_recall_is_na():
    """Test 1: Zero expected causes in ground truth produces Recall = None (N/A), NOT 100%."""
    gt_no_causes = CaseGroundTruth(
        case_id="CASE-NO-CAUSE",
        settlement_id="setl_test",
        scenario=ScenarioType.COMPLETELY_UNEXPLAINED,
        expected_variance=10000,
        true_causes=[],
        decoys=[],
        explained_amount=0,
        unexplained_amount=10000,
        expected_outcome=ExpectedOutcome.ESCALATE,
        notes="Unexplained",
    )
    result = RetrievalResult(
        case_id="CASE-NO-CAUSE",
        settlement_id="setl_test",
        strategy=RetrievalStrategy.RELATIONSHIP,
        target_variance=10000,
        candidates=[],
        is_applicable=True,
    )
    eval_row = RetrievalEvaluator.evaluate_scenario(result, gt_no_causes)
    assert eval_row.recall_pct is None  # Must be N/A


def test_evaluator_zero_expected_and_zero_candidates_precision_is_na():
    """Test 2: Zero expected causes and zero candidates retrieved produces Precision = None (N/A)."""
    gt = CaseGroundTruth(
        case_id="CASE-01",
        settlement_id="setl_01",
        scenario=ScenarioType.COMPLETELY_UNEXPLAINED,
        expected_variance=5000,
        true_causes=[],
        decoys=[],
        explained_amount=0,
        unexplained_amount=5000,
        expected_outcome=ExpectedOutcome.ESCALATE,
        notes="",
    )
    res = RetrievalResult(
        case_id="CASE-01",
        settlement_id="setl_01",
        strategy=RetrievalStrategy.RELATIONSHIP,
        target_variance=5000,
        candidates=[],
        is_applicable=True,
    )
    eval_row = RetrievalEvaluator.evaluate_scenario(res, gt)
    assert eval_row.precision_pct is None  # Must be N/A


def test_evaluator_expected_causes_with_zero_candidates_precision_is_zero():
    """Test 3: Expected causes exist but zero candidates retrieved produces Precision = 0.0%."""
    gt = CaseGroundTruth(
        case_id="CASE-02",
        settlement_id="setl_02",
        scenario=ScenarioType.REFUND_VARIANCE,
        expected_variance=5000,
        true_causes=[GroundTruthCause(entity_type="refund", entity_id="rfnd_01", amount=-5000)],
        decoys=[],
        explained_amount=5000,
        unexplained_amount=0,
        expected_outcome=ExpectedOutcome.RESOLVED,
        notes="",
    )
    res = RetrievalResult(
        case_id="CASE-02",
        settlement_id="setl_02",
        strategy=RetrievalStrategy.RELATIONSHIP,
        target_variance=5000,
        candidates=[],
        is_applicable=True,
    )
    eval_row = RetrievalEvaluator.evaluate_scenario(res, gt)
    assert eval_row.precision_pct == 0.0
    assert eval_row.recall_pct == 0.0


def test_evaluator_no_decoys_rejection_is_na():
    """Test 4: Scenario with zero known decoys produces Decoy Rejection = None (N/A), NOT 100%."""
    gt = CaseGroundTruth(
        case_id="CASE-03",
        settlement_id="setl_03",
        scenario=ScenarioType.REFUND_VARIANCE,
        expected_variance=5000,
        true_causes=[GroundTruthCause(entity_type="refund", entity_id="rfnd_01", amount=-5000)],
        decoys=[],
        explained_amount=5000,
        unexplained_amount=0,
        expected_outcome=ExpectedOutcome.RESOLVED,
        notes="",
    )
    res = RetrievalResult(
        case_id="CASE-03",
        settlement_id="setl_03",
        strategy=RetrievalStrategy.RELATIONSHIP,
        target_variance=5000,
        candidates=[EvidenceCandidate(candidate_id="c1", entity_type="refund", entity_id="rfnd_01", amount=5000, relationship_path="rel")],
        is_applicable=True,
    )
    eval_row = RetrievalEvaluator.evaluate_scenario(res, gt)
    assert eval_row.decoy_rejection_pct is None  # Must be N/A


def test_evaluator_aggregate_metrics_ignore_na():
    """Test 5 & 6: Aggregate metrics calculate averages strictly over defined (non-N/A) cases."""
    rows = [
        ScenarioEvaluationRow(
            scenario_id="S1", strategy=RetrievalStrategy.RELATIONSHIP, task_category=InvestigationTaskCategory.SETTLEMENT_RCA,
            case_id="C1", settlement_id="setl_1", target_variance_inr=100.0, is_applicable=True,
            true_causes_expected=2, true_causes_retrieved=2, recall_pct=100.0, candidates_retrieved=4, precision_pct=50.0,
            decoys_present=1, decoys_rejected=1, decoy_rejection_pct=100.0, provenance_coverage_pct=100.0, latency_ms=0.1,
        ),
        ScenarioEvaluationRow(
            scenario_id="S2", strategy=RetrievalStrategy.RELATIONSHIP, task_category=InvestigationTaskCategory.SETTLEMENT_RCA,
            case_id="C2", settlement_id="setl_2", target_variance_inr=50.0, is_applicable=True,
            true_causes_expected=0, true_causes_retrieved=0, recall_pct=None, candidates_retrieved=0, precision_pct=None,
            decoys_present=0, decoys_rejected=0, decoy_rejection_pct=None, provenance_coverage_pct=None, latency_ms=0.1,
        ),
    ]
    metrics = RetrievalEvaluator.aggregate_strategy_metrics(RetrievalStrategy.RELATIONSHIP, rows)

    assert metrics.applicable_cases == 2
    assert metrics.evidence_recall_pct == 100.0  # (2 / 2)
    assert metrics.candidate_precision_pct == 50.0  # (2 / 4)
    assert metrics.decoy_rejection_rate_pct == 100.0  # (1 / 1)
    assert metrics.provenance_coverage_pct == 100.0


# ==========================================
# 2. UPI Evidence Retrieval Tests
# ==========================================

def test_upi_retrieval_var_005_late_success(retrieval_test_env):
    """Test 7 & 8: VAR-005 retrieves exact UPI transaction with 3 supporting chronological events."""
    dataset = retrieval_test_env["dataset"]
    strategy = UPIEventRetrievalStrategy()

    target_setl = next((s for s in dataset.settlements if "scen_005" in s.id), None)
    assert target_setl is not None

    res = strategy.retrieve(
        case_id="CASE-005", settlement_id=target_setl.id, target_variance=0,
        dataset=dataset, task_category=InvestigationTaskCategory.UPI_STATE_INVESTIGATION
    )

    assert res.is_applicable is True
    # Exactly 1 root UPITransaction candidate (no candidate explosion!)
    assert len(res.candidates) == 1
    root_cand = res.candidates[0]

    assert root_cand.entity_type == "upi_transaction"
    assert "scen_005" in root_cand.entity_id
    assert root_cand.evidence_metadata["evidence_classification"] == "LATE_SUCCESS"
    assert len(root_cand.supporting_events) == 3

    # Check discrete event transitions
    transitions = [e["transition"] for e in root_cand.supporting_events]
    assert "INITIATED → PENDING" in transitions
    assert "PENDING → FAILED" in transitions
    assert "FAILED → CAPTURED" in transitions


def test_upi_retrieval_var_006_no_candidate_explosion(retrieval_test_env):
    """Test 9 & 10: VAR-006 retrieves the debit+reversal chain without returning hundreds of candidates."""
    dataset = retrieval_test_env["dataset"]
    strategy = UPIEventRetrievalStrategy()

    res = strategy.retrieve(
        case_id="CASE-006", settlement_id="N/A", target_variance=0,
        dataset=dataset, task_category=InvestigationTaskCategory.UPI_STATE_INVESTIGATION
    )

    assert res.is_applicable is True
    # Must NOT return hundreds of transactions; returns exactly 1 matched candidate
    assert len(res.candidates) == 1
    root_cand = res.candidates[0]

    assert root_cand.evidence_metadata["evidence_classification"] == "DEBIT_REVERSED"
    assert root_cand.evidence_metadata["reversal_status"] == "SUCCESS"
    assert root_cand.net_financial_effect == 0  # Type-safe net financial effect = 0
    assert len(root_cand.supporting_events) == 2


def test_upi_retrieval_amount_only_fallback_marked_low_confidence(retrieval_test_env):
    """Test 11 & 12: Unsettled amount-only UPI match is explicitly marked IDENTITY_CONFIDENCE = LOW."""
    dataset = retrieval_test_env["dataset"]
    strategy = UPIEventRetrievalStrategy()

    # Query with generic unknown case ID and target variance amount
    res = strategy.retrieve(
        case_id="CASE-GENERIC-UNSETTLED", settlement_id="N/A", target_variance=500000,
        dataset=dataset, task_category=InvestigationTaskCategory.UPI_STATE_INVESTIGATION
    )

    assert res.is_applicable is True
    assert len(res.candidates) >= 1
    assert res.candidates[0].identity_confidence == "LOW"


# ==========================================
# 3. Strategy Applicability & Benchmark Tests
# ==========================================

def test_non_applicable_strategies_marked_na(retrieval_test_env):
    """Test 13: Strategies not designed for a specific task category are marked is_applicable=False."""
    dataset = retrieval_test_env["dataset"]
    upi_strategy = UPIEventRetrievalStrategy()
    rel_strategy = RelationshipAwareRetrievalStrategy()

    # UPI strategy on Settlement RCA case -> NOT applicable
    upi_res = upi_strategy.retrieve(
        case_id="CASE-001", settlement_id="setl_scen_001", target_variance=-200000,
        dataset=dataset, task_category=InvestigationTaskCategory.SETTLEMENT_RCA
    )
    assert upi_res.is_applicable is False

    # Relationship strategy on UPI State Investigation -> NOT applicable
    rel_res = rel_strategy.retrieve(
        case_id="CASE-005", settlement_id="setl_scen_005", target_variance=0,
        dataset=dataset, task_category=InvestigationTaskCategory.UPI_STATE_INVESTIGATION
    )
    assert rel_res.is_applicable is False


def test_full_benchmark_runner_matrix(retrieval_test_env):
    """Test 14 & 15: Run benchmark runner across all 10 scenarios and verify clean N/A reporting."""
    dataset = retrieval_test_env["dataset"]
    gt_path = retrieval_test_env["gt_path"]
    exp_dir = retrieval_test_env["exp_dir"]

    runner = RetrievalBenchmarkRunner()
    report = runner.run_all_experiments(dataset, gt_path, export_dir=exp_dir)

    assert report.total_experiments_run == 60
    assert (Path(exp_dir) / "results.json").exists()
    assert (Path(exp_dir) / "results.csv").exists()

    # Verify DIRECT_ID, RELATIONSHIP, TEMPORAL_RELATIONSHIP have 8 applicable cases
    assert report.strategy_metrics["DIRECT_ID"].applicable_cases == 8
    assert report.strategy_metrics["RELATIONSHIP"].applicable_cases == 8
    assert report.strategy_metrics["TEMPORAL_RELATIONSHIP"].applicable_cases == 8

    # Verify UPI_EVENT has 2 applicable cases and 100% recall on its task
    assert report.strategy_metrics["UPI_EVENT"].applicable_cases == 2
    assert report.strategy_metrics["UPI_EVENT"].evidence_recall_pct == 100.0

    # Verify TEMPORAL_RELATIONSHIP achieves highest precision and 100% decoy rejection on its task
    temp_metrics = report.strategy_metrics["TEMPORAL_RELATIONSHIP"]
    assert temp_metrics.evidence_recall_pct == 100.0
    assert temp_metrics.decoy_rejection_rate_pct == 100.0
    assert temp_metrics.candidate_precision_pct > 35.0
