from pathlib import Path
import pytest

from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestionPipeline
from neofinesse.investigation.benchmark import InvestigationBenchmarkRunner
from neofinesse.investigation.constraints import (
    MonetaryConstraint,
    ProvenanceConstraint,
    RelationshipConstraint,
    StateConstraint,
    TemporalConstraint,
)
from neofinesse.investigation.hypothesis import HypothesisBuilder
from neofinesse.investigation.investigator import VarianceInvestigator
from neofinesse.investigation.models import (
    CauseType,
    ConstraintStatus,
    HypothesisStatus,
    InvestigationStatus,
)
from neofinesse.models.base import EvidenceLevel, ProvenanceReference, SourceType
from neofinesse.retrieval.base import EvidenceCandidate, InvestigationTaskCategory


@pytest.fixture(scope="module")
def investigation_test_env(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("phase5_env")
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
# 1. Scenario Verification Tests (VAR-001 - VAR-010)
# ==========================================

def test_var_001_single_refund_resolved(investigation_test_env):
    """Test 1: VAR-001 single processed refund is verified and resolved."""
    dataset = investigation_test_env["dataset"]
    investigator = VarianceInvestigator()

    target_setl = next(s for s in dataset.settlements if "scen_001" in s.id)
    res = investigator.investigate(
        case_id="CASE-001",
        settlement_id=target_setl.id,
        target_variance=-200000,
        dataset=dataset,
        task_category=InvestigationTaskCategory.SETTLEMENT_RCA,
    )

    assert res.final_status == InvestigationStatus.RESOLVED
    assert res.winning_hypothesis is not None
    assert res.winning_hypothesis.cause_type == CauseType.REFUND
    assert res.winning_hypothesis.evidence_level == EvidenceLevel.L5
    assert res.explained_amount == -200000
    assert res.unexplained_amount == 0


def test_var_002_same_amount_decoy_rejected(investigation_test_env):
    """Test 2: VAR-002 accepts real refund and explicitly rejects same-amount decoy in other settlement."""
    dataset = investigation_test_env["dataset"]
    investigator = VarianceInvestigator()

    target_setl = next(s for s in dataset.settlements if "scen_002" in s.id)
    res = investigator.investigate(
        case_id="CASE-002",
        settlement_id=target_setl.id,
        target_variance=-250000,
        dataset=dataset,
        task_category=InvestigationTaskCategory.SETTLEMENT_RCA,
    )

    assert res.final_status == InvestigationStatus.RESOLVED
    assert res.winning_hypothesis is not None
    # Real refund must win
    assert "real" in res.winning_hypothesis.evidence_ids[0]

    # Decoy must not be in winning hypothesis
    assert not any("decoy" in eid for eid in res.winning_hypothesis.evidence_ids)


def test_var_003_partial_attribution_residual_preserved(investigation_test_env):
    """Test 3: VAR-003 attributes ₹3,000 refund and strictly preserves ₹2,000 unexplained residual."""
    dataset = investigation_test_env["dataset"]
    investigator = VarianceInvestigator()

    target_setl = next(s for s in dataset.settlements if "scen_003" in s.id)
    res = investigator.investigate(
        case_id="CASE-003",
        settlement_id=target_setl.id,
        target_variance=-500000,  # ₹5,000 short
        dataset=dataset,
        task_category=InvestigationTaskCategory.SETTLEMENT_RCA,
    )

    assert res.final_status == InvestigationStatus.PARTIALLY_RESOLVED
    assert res.winning_hypothesis is not None
    assert res.winning_hypothesis.status == HypothesisStatus.PARTIALLY_VERIFIED
    assert res.explained_amount == -300000  # ₹3,000 refund explained
    assert res.unexplained_amount == -200000  # ₹2,000 remaining


def test_var_004_multi_event_explanation_resolved(investigation_test_env):
    """Test 4: VAR-004 verifies composite multi-event explanation (₹700 refund + ₹300 adjustment = ₹1,000)."""
    dataset = investigation_test_env["dataset"]
    investigator = VarianceInvestigator()

    target_setl = next(s for s in dataset.settlements if "scen_004" in s.id)
    res = investigator.investigate(
        case_id="CASE-004",
        settlement_id=target_setl.id,
        target_variance=-100000,
        dataset=dataset,
        task_category=InvestigationTaskCategory.SETTLEMENT_RCA,
    )

    assert res.final_status == InvestigationStatus.RESOLVED
    assert res.winning_hypothesis is not None
    assert res.winning_hypothesis.cause_type == CauseType.COMPOSITE
    assert len(res.winning_hypothesis.candidate_evidence) == 2
    assert res.explained_amount == -100000
    assert res.unexplained_amount == 0


def test_var_005_upi_late_success(investigation_test_env):
    """Test 5: VAR-005 verifies UPI late success lifecycle transition."""
    dataset = investigation_test_env["dataset"]
    investigator = VarianceInvestigator()

    target_setl = next(s for s in dataset.settlements if "scen_005" in s.id)
    res = investigator.investigate(
        case_id="CASE-005",
        settlement_id=target_setl.id,
        target_variance=0,
        dataset=dataset,
        task_category=InvestigationTaskCategory.UPI_STATE_INVESTIGATION,
    )

    assert res.final_status == InvestigationStatus.RESOLVED
    assert res.winning_hypothesis is not None
    assert res.winning_hypothesis.cause_type == CauseType.UPI_STATE
    assert res.winning_hypothesis.hypothesis_metadata.get("upi_classification") == "LATE_SUCCESS"


def test_var_006_upi_debit_reversal(investigation_test_env):
    """Test 6: VAR-006 verifies debit + reversal chain producing net zero financial effect."""
    dataset = investigation_test_env["dataset"]
    investigator = VarianceInvestigator()

    res = investigator.investigate(
        case_id="CASE-006",
        settlement_id="N/A",
        target_variance=0,
        dataset=dataset,
        task_category=InvestigationTaskCategory.UPI_STATE_INVESTIGATION,
    )

    assert res.final_status == InvestigationStatus.RESOLVED
    assert res.winning_hypothesis is not None
    assert res.winning_hypothesis.cause_type == CauseType.UPI_STATE
    assert res.winning_hypothesis.hypothesis_metadata.get("upi_classification") == "DEBIT_REVERSED"
    assert res.explained_amount == 0


def test_var_007_delayed_bank_credit(investigation_test_env):
    """Test 7: VAR-007 recognizes valid delayed bank settlement credit."""
    dataset = investigation_test_env["dataset"]
    investigator = VarianceInvestigator()

    target_setl = next(s for s in dataset.settlements if "scen_007" in s.id)
    res = investigator.investigate(
        case_id="CASE-007",
        settlement_id=target_setl.id,
        target_variance=0,
        dataset=dataset,
        task_category=InvestigationTaskCategory.BANK_SETTLEMENT_STATE,
    )

    assert res.final_status == InvestigationStatus.VALID_DELAYED_CREDIT


def test_var_008_wrong_date_decoy_escalated(investigation_test_env):
    """Test 8: VAR-008 rejects post-cutoff refund (fails temporal constraint) and escalates."""
    dataset = investigation_test_env["dataset"]
    investigator = VarianceInvestigator()

    target_setl = next(s for s in dataset.settlements if "scen_008" in s.id)
    res = investigator.investigate(
        case_id="CASE-008",
        settlement_id=target_setl.id,
        target_variance=-400000,
        dataset=dataset,
        task_category=InvestigationTaskCategory.SETTLEMENT_RCA,
    )

    assert res.final_status == InvestigationStatus.ESCALATE
    assert res.winning_hypothesis is None
    assert res.unexplained_amount == -400000


def test_var_009_wrong_payment_decoy_escalated(investigation_test_env):
    """Test 9: VAR-009 rejects dispute on unrelated payment (fails relationship constraint) and escalates."""
    dataset = investigation_test_env["dataset"]
    investigator = VarianceInvestigator()

    target_setl = next(s for s in dataset.settlements if "scen_009" in s.id)
    res = investigator.investigate(
        case_id="CASE-009",
        settlement_id=target_setl.id,
        target_variance=-350000,
        dataset=dataset,
        task_category=InvestigationTaskCategory.SETTLEMENT_RCA,
    )

    assert res.final_status == InvestigationStatus.ESCALATE
    assert res.winning_hypothesis is None
    assert res.unexplained_amount == -350000


def test_var_010_completely_unexplained_escalated(investigation_test_env):
    """Test 10: VAR-010 finds no valid causal deduction events and honestly escalates."""
    dataset = investigation_test_env["dataset"]
    investigator = VarianceInvestigator()

    target_setl = next(s for s in dataset.settlements if "scen_010" in s.id)
    res = investigator.investigate(
        case_id="CASE-010",
        settlement_id=target_setl.id,
        target_variance=-1500000,
        dataset=dataset,
        task_category=InvestigationTaskCategory.SETTLEMENT_RCA,
    )

    assert res.final_status == InvestigationStatus.ESCALATE
    assert res.winning_hypothesis is None
    assert res.unexplained_amount == -1500000


# ==========================================
# 2. Independent Constraint Unit Tests
# ==========================================

def test_monetary_constraint_overage_fails():
    """Test 11: Candidate amount exceeding target variance fails MonetaryConstraint."""
    cand = EvidenceCandidate(candidate_id="c1", entity_type="refund", entity_id="r1", amount=600000, relationship_path="path")
    h = HypothesisBuilder.create_hypothesis("h1", "case1", CauseType.REFUND, [cand], target_variance=-500000, explanation="test")
    res = MonetaryConstraint.evaluate(h, target_variance=-500000)
    assert res.status == ConstraintStatus.FAIL
    assert "exceeds target variance" in res.reason


def test_provenance_constraint_missing_hash_fails():
    """Test 12: Evidence with incomplete hash or file provenance fails ProvenanceConstraint."""
    from datetime import datetime
    from neofinesse.models.base import Provider

    prov_incomplete = ProvenanceReference(
        source_id="SRC-1", source_type=SourceType.CSV, source_file="refunds.csv", source_row=5,
        source_hash="", record_hash="", provider=Provider.RAZORPAY, ingested_at=datetime.now(), ingested_by="test"
    )
    cand = EvidenceCandidate(candidate_id="c1", entity_type="refund", entity_id="r1", amount=5000, relationship_path="path", provenance=prov_incomplete)
    h = HypothesisBuilder.create_hypothesis("h1", "case1", CauseType.REFUND, [cand], target_variance=-5000, explanation="test")
    res = ProvenanceConstraint.evaluate(h)
    assert res.status == ConstraintStatus.FAIL


def test_counterfactual_residual_calculation():
    """Test 13: Excluding a constituent candidate restores the residual unexplained variance."""
    c1 = EvidenceCandidate(candidate_id="c1", entity_type="refund", entity_id="rfnd_1", amount=70000, net_financial_effect=-70000, relationship_path="p1")
    c2 = EvidenceCandidate(candidate_id="c2", entity_type="adjustment", entity_id="adj_1", amount=30000, net_financial_effect=-30000, relationship_path="p2")

    h = HypothesisBuilder.create_hypothesis("h1", "case1", CauseType.COMPOSITE, [c1, c2], target_variance=-100000, explanation="composite")

    # When both are present, residual is 0
    assert HypothesisBuilder.compute_counterfactual_residual(h) == 0

    # When c1 is excluded, residual is -70,000 paise (-₹700)
    assert HypothesisBuilder.compute_counterfactual_residual(h, excluded_candidate_id="rfnd_1") == -70000

    # When c2 is excluded, residual is -30,000 paise (-₹300)
    assert HypothesisBuilder.compute_counterfactual_residual(h, excluded_candidate_id="adj_1") == -30000


# ==========================================
# 3. Benchmark Scorecard Test
# ==========================================

def test_phase5_benchmark_scorecard_perfect_safety(investigation_test_env):
    """Test 14: Phase 5 benchmark achieves 100% Root Cause Accuracy and 0% False Closure Rate."""
    dataset = investigation_test_env["dataset"]
    gt_path = investigation_test_env["gt_path"]
    exp_dir = investigation_test_env["exp_dir"]

    runner = InvestigationBenchmarkRunner()
    scorecard = runner.run_benchmark(dataset, gt_path, export_dir=exp_dir)

    assert scorecard.total_scenarios_evaluated == 10
    assert scorecard.correct_outcomes == 10
    assert scorecard.root_cause_accuracy_pct == 100.0
    assert scorecard.false_closures == 0
    assert scorecard.false_closure_rate_pct == 0.0
    assert scorecard.partial_attribution_accuracy_pct == 100.0
    assert scorecard.honest_exception_rate_pct == 100.0
    assert scorecard.avg_latency_ms < 5.0  # Ultra fast deterministic evaluation

    assert (Path(exp_dir) / "results.json").exists()
    assert (Path(exp_dir) / "results.csv").exists()
