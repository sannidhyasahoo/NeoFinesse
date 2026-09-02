from datetime import datetime, timedelta
import pytest

from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestionPipeline
from neofinesse.models.base import EvidenceLevel, FinalDeterminedStatus, FinancialEffectStatus, NormalizedObservedStatus, ReversalStatus, SettlementReconStatus
from neofinesse.models.events import Payment
from neofinesse.models.settlement import Settlement, SettlementLine
from neofinesse.models.upi import UPIEvent, UPITransaction
from neofinesse.models.bank import BankTransaction
from neofinesse.reconciliation.candidates import CandidateRetriever
from neofinesse.reconciliation.engine import DeterministicReconciliationEngine
from neofinesse.reconciliation.joins import BankJoinEngine, BankJoinStatus
from neofinesse.reconciliation.metrics import BaselineEvaluator
from neofinesse.reconciliation.solver import MultiConstraintAttributionSolver
from neofinesse.reconciliation.temporal import TemporalConstraintFilter
from neofinesse.reconciliation.upi_state import UPIStateReconstructor


@pytest.fixture
def reconciled_dataset(tmp_path):
    data_dir = tmp_path / "data"
    gt_dir = tmp_path / "ground_truth"

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

    engine = DeterministicReconciliationEngine()
    run_result = engine.run(dataset)

    return {
        "dataset": dataset,
        "run_result": run_result,
        "gt_path": export_meta["ground_truth_path"],
    }


def test_bank_utr_matching():
    """Test BankJoinEngine with exact match, delayed credit, and missing bank transaction."""
    join_engine = BankJoinEngine(max_clearing_window_hours=48.0)
    t = datetime(2026, 8, 1, 10, 0, 0)

    s1 = Settlement(id="setl_01", amount=100000, expected_amount=100000, utr="AXISCN112233", created_at=t, settled_at=t)
    s2 = Settlement(id="setl_02", amount=200000, expected_amount=200000, utr="HDFCN445566", recon_status=SettlementReconStatus.PENDING_BANK_CREDIT, created_at=t, settled_at=t)
    s3 = Settlement(id="setl_03", amount=300000, expected_amount=300000, utr="NO_BANK_MATCH", created_at=t, settled_at=t)

    b1 = BankTransaction(bank_txn_id="b1", utr="AXISCN112233", credit_amount=100000, value_date=t, transaction_date=t, raw_description="AXISCN112233")
    b2 = BankTransaction(bank_txn_id="b2", utr="HDFCN445566", credit_amount=200000, value_date=t + timedelta(hours=24), transaction_date=t + timedelta(hours=24), raw_description="HDFCN445566")

    results = join_engine.match_settlements_to_bank([s1, s2, s3], [b1, b2])

    assert results["setl_01"].join_status == BankJoinStatus.EXACT_UTR_MATCH
    assert results["setl_02"].join_status == BankJoinStatus.DELAYED_BANK_CREDIT
    assert results["setl_03"].join_status == BankJoinStatus.MISSING_BANK_TRANSACTION


def test_upi_state_reconstruction_scenarios():
    """Test UPIStateReconstructor with clean failure, debit+reversal, late success, and unconfirmed debit."""
    reconstructor = UPIStateReconstructor()
    t = datetime(2026, 8, 1, 10, 0, 0)

    # 1. Late success
    u1 = UPITransaction(
        upi_transaction_id="u1", payment_id="p1", amount=350000, initiated_at=t,
        current_observed_status=NormalizedObservedStatus.CAPTURED,
        final_determined_status=FinalDeterminedStatus.LATE_SUCCESS,
    )
    events_u1 = [
        UPIEvent(event_id="e1", upi_transaction_id="u1", timestamp=t, previous_state=NormalizedObservedStatus.INITIATED, new_state=NormalizedObservedStatus.PENDING, event_type="INIT"),
        UPIEvent(event_id="e2", upi_transaction_id="u1", timestamp=t + timedelta(minutes=5), previous_state=NormalizedObservedStatus.PENDING, new_state=NormalizedObservedStatus.FAILED, event_type="TIMEOUT"),
        UPIEvent(event_id="e3", upi_transaction_id="u1", timestamp=t + timedelta(minutes=25), previous_state=NormalizedObservedStatus.FAILED, new_state=NormalizedObservedStatus.CAPTURED, event_type="LATE_AUTH"),
    ]
    res1 = reconstructor.reconstruct(u1, events_u1)
    assert res1.determined_status == FinalDeterminedStatus.LATE_SUCCESS
    assert res1.financial_effect_status == FinancialEffectStatus.DETERMINED
    assert res1.financial_effect_amount == 350000

    # 2. Debit + confirmed reversal -> net 0
    u2 = UPITransaction(
        upi_transaction_id="u2", payment_id="p2", amount=500000, initiated_at=t,
        current_observed_status=NormalizedObservedStatus.FAILED,
        final_determined_status=FinalDeterminedStatus.FAILED,
        debit_observed=True, reversal_status=ReversalStatus.SUCCESS, reversal_amount=500000,
    )
    events_u2 = [
        UPIEvent(event_id="e4", upi_transaction_id="u2", timestamp=t, previous_state=NormalizedObservedStatus.INITIATED, new_state=NormalizedObservedStatus.FAILED, event_type="DEBIT_TIMEOUT"),
        UPIEvent(event_id="e5", upi_transaction_id="u2", timestamp=t + timedelta(minutes=10), previous_state=NormalizedObservedStatus.FAILED, new_state=NormalizedObservedStatus.FAILED, event_type="AUTO_REVERSAL_CONFIRMATION"),
    ]
    res2 = reconstructor.reconstruct(u2, events_u2)
    assert res2.determined_status == FinalDeterminedStatus.FAILED
    assert res2.financial_effect_status == FinancialEffectStatus.DETERMINED
    assert res2.financial_effect_amount == 0

    # 3. Debit observed but no reversal evidence -> UNKNOWN
    u3 = UPITransaction(
        upi_transaction_id="u3", payment_id="p3", amount=400000, initiated_at=t,
        current_observed_status=NormalizedObservedStatus.FAILED,
        final_determined_status=FinalDeterminedStatus.FAILED,
        debit_observed=True, reversal_status=ReversalStatus.NONE,
    )
    events_u3 = [
        UPIEvent(event_id="e6", upi_transaction_id="u3", timestamp=t, previous_state=NormalizedObservedStatus.INITIATED, new_state=NormalizedObservedStatus.FAILED, event_type="DEBIT_TIMEOUT"),
    ]
    res3 = reconstructor.reconstruct(u3, events_u3)
    assert res3.financial_effect_status == FinancialEffectStatus.UNKNOWN
    assert res3.financial_effect_amount is None


def test_temporal_filter_cutoff_rejection():
    """Test TemporalConstraintFilter rejecting post-cutoff candidate events."""
    temp_filter = TemporalConstraintFilter(allowable_lead_buffer_hours=2.0)
    t = datetime(2026, 8, 1, 10, 0, 0)
    settlement = Settlement(id="setl_01", amount=100000, expected_amount=100000, created_at=t, settled_at=t)

    from neofinesse.reconciliation.candidates import CandidateEvent
    valid_cand = CandidateEvent(
        candidate_id="c1", entity_type="refund", entity_id="r1", amount=10000, net_financial_effect=-10000,
        relationship_path="rel", timestamp=t - timedelta(hours=2),
    )
    post_cutoff_cand = CandidateEvent(
        candidate_id="c2", entity_type="refund", entity_id="r2", amount=10000, net_financial_effect=-10000,
        relationship_path="rel", timestamp=t + timedelta(days=15),
    )

    is_valid1, status1, _ = temp_filter.validate_candidate_timing(valid_cand, settlement)
    assert is_valid1 is True

    is_valid2, status2, _ = temp_filter.validate_candidate_timing(post_cutoff_cand, settlement)
    assert is_valid2 is False
    assert status2 == "OUTSIDE_WINDOW"


def test_end_to_end_benchmark_scorecard(reconciled_dataset):
    """Test BaselineEvaluator achieving 100% accuracy and 0 false closures on all 10 ground truth scenarios."""
    run_result = reconciled_dataset["run_result"]
    gt_path = reconciled_dataset["gt_path"]

    scorecard = BaselineEvaluator.evaluate(run_result, gt_path)

    assert scorecard.total_scenarios_evaluated == 10
    assert scorecard.correct_outcomes == 10
    assert scorecard.accuracy_percentage == 100.0
    assert scorecard.false_causes_accepted == 0
    assert scorecard.false_closures == 0
    assert scorecard.true_cause_recall_percentage >= 90.0
