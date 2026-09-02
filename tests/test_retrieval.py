import shutil
from pathlib import Path
import pytest

from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestedDataset, IngestionPipeline
from neofinesse.models.base import ProvenanceReference, SourceType
from neofinesse.models.ground_truth import CaseGroundTruth
from neofinesse.retrieval.attribute import AttributeRetrievalStrategy
from neofinesse.retrieval.base import RetrievalStrategy, TemporalRetrievalStatus
from neofinesse.retrieval.benchmark import RetrievalBenchmarkRunner
from neofinesse.retrieval.direct_id import DirectIdRetrievalStrategy
from neofinesse.retrieval.provenance import TypedProvenanceRetrievalStrategy
from neofinesse.retrieval.relationship import RelationshipAwareRetrievalStrategy
from neofinesse.retrieval.temporal import TemporalRelationshipRetrievalStrategy
from neofinesse.retrieval.upi_event import UPIEventRetrievalStrategy


@pytest.fixture(scope="module")
def retrieval_test_env(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("phase4_env")
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


def test_direct_id_retrieval(retrieval_test_env):
    """Test 1: Direct ID retrieval retrieves only explicit key records."""
    dataset = retrieval_test_env["dataset"]
    strategy = DirectIdRetrievalStrategy()

    sample_setl = dataset.settlements[0]
    res = strategy.retrieve(case_id="TEST-01", settlement_id=sample_setl.id, target_variance=0, dataset=dataset)

    assert res.strategy == RetrievalStrategy.DIRECT_ID
    assert len(res.candidates) > 0

    # Ensure all retrieved candidates have explicit links to this settlement
    for c in res.candidates:
        assert (
            sample_setl.id in c.relationship_path
            or c.entity_id in [l.source_event_id for l in dataset.settlement_lines if l.settlement_id == sample_setl.id]
            or c.entity_id == sample_setl.id
            or (sample_setl.utr and sample_setl.utr in c.relationship_path)
        )


def test_attribute_retrieval_captures_decoys(retrieval_test_env):
    """Test 2 & 3: Attribute retrieval matches globally and intentionally captures decoys."""
    dataset = retrieval_test_env["dataset"]
    attr_strategy = AttributeRetrievalStrategy()
    rel_strategy = RelationshipAwareRetrievalStrategy()

    # In VAR-002, variance is ₹2,500 (250000 paise). Real refund is in setl_scen_002, decoy refund is in other settlement.
    target_amount = -250000
    target_setl = next((s for s in dataset.settlements if "scen_002" in s.id), None)
    assert target_setl is not None

    attr_res = attr_strategy.retrieve(case_id="TEST-02", settlement_id=target_setl.id, target_variance=target_amount, dataset=dataset)
    rel_res = rel_strategy.retrieve(case_id="TEST-02", settlement_id=target_setl.id, target_variance=target_amount, dataset=dataset)

    # Attribute strategy should capture >= 2 candidates (real + decoy)
    attr_cands = [c.entity_id for c in attr_res.candidates]
    assert len(attr_cands) >= 2
    assert any("decoy" in cid for cid in attr_cands)

    # Relationship strategy should reject the decoy and only keep the real refund in candidates
    rel_cands = [c.entity_id for c in rel_res.candidates]
    assert any("real" in cid for cid in rel_cands)
    assert not any("decoy" in cid for cid in rel_cands)

    # Ensure the decoy is explicitly recorded in rejected_candidates
    rejected_ids = [r.entity_id for r in rel_res.rejected_candidates]
    assert any("decoy" in rid for rid in rejected_ids)


def test_relationship_rejection_of_wrong_payment(retrieval_test_env):
    """Test 4: Relationship retrieval rejects dispute belonging to another payment (VAR-009)."""
    dataset = retrieval_test_env["dataset"]
    rel_strategy = RelationshipAwareRetrievalStrategy()

    target_setl = next((s for s in dataset.settlements if "scen_009" in s.id), None)
    assert target_setl is not None

    res = rel_strategy.retrieve(case_id="TEST-09", settlement_id=target_setl.id, target_variance=350000, dataset=dataset)

    # Decoy dispute disp_scen_009_decoy must NOT be in active candidates
    cand_ids = [c.entity_id for c in res.candidates]
    assert not any("decoy" in cid for cid in cand_ids)

    # Must be in rejected_candidates with relationship mismatch reason
    rej_reasons = [r.rejection_reason for r in res.rejected_candidates if "decoy" in r.entity_id]
    assert len(rej_reasons) > 0
    assert "unrelated payment" in rej_reasons[0].lower() or "unrelated settlement" in rej_reasons[0].lower()


def test_temporal_rejection_of_wrong_date(retrieval_test_env):
    """Test 5: TemporalRelationship retrieval rejects post-cutoff refund (VAR-008)."""
    dataset = retrieval_test_env["dataset"]
    temp_strategy = TemporalRelationshipRetrievalStrategy()

    target_setl = next((s for s in dataset.settlements if "scen_008" in s.id), None)
    assert target_setl is not None

    res = temp_strategy.retrieve(case_id="TEST-08", settlement_id=target_setl.id, target_variance=400000, dataset=dataset)

    # Post-cutoff refund must be rejected and recorded in rejected_candidates with OUTSIDE_WINDOW reason
    rej_decoy = [r for r in res.rejected_candidates if "decoy" in r.entity_id]
    assert len(rej_decoy) > 0
    assert "after settlement cutoff" in rej_decoy[0].rejection_reason.lower()


def test_multiple_event_retrieval(retrieval_test_env):
    """Test 6: Multiple event explanation (VAR-004) retrieves both refund and adjustment."""
    dataset = retrieval_test_env["dataset"]
    rel_strategy = RelationshipAwareRetrievalStrategy()

    target_setl = next((s for s in dataset.settlements if "scen_004" in s.id), None)
    assert target_setl is not None

    res = rel_strategy.retrieve(case_id="TEST-04", settlement_id=target_setl.id, target_variance=-100000, dataset=dataset)

    types = {c.entity_type for c in res.candidates}
    assert "refund" in types
    assert "adjustment" in types

    rfnd_cand = next(c for c in res.candidates if c.entity_type == "refund")
    adj_cand = next(c for c in res.candidates if c.entity_type == "adjustment")

    assert rfnd_cand.amount == 70000  # ₹700
    assert adj_cand.amount == 30000   # ₹300


def test_partial_explanation_retrieval(retrieval_test_env):
    """Test 7: Partial explanation (VAR-003) retrieves valid refund of ₹3,000 for ₹5,000 variance."""
    dataset = retrieval_test_env["dataset"]
    rel_strategy = RelationshipAwareRetrievalStrategy()

    target_setl = next((s for s in dataset.settlements if "scen_003" in s.id), None)
    assert target_setl is not None

    res = rel_strategy.retrieve(case_id="TEST-03", settlement_id=target_setl.id, target_variance=200000, dataset=dataset)

    # Must retrieve the valid constituent refund of ₹3,000
    refund_cands = [c for c in res.candidates if c.entity_type == "refund"]
    assert len(refund_cands) >= 1
    assert refund_cands[0].amount == 300000


def test_completely_unexplained_retrieval(retrieval_test_env):
    """Test 8: Completely unexplained variance (VAR-010) returns no false causal candidates."""
    dataset = retrieval_test_env["dataset"]
    rel_strategy = RelationshipAwareRetrievalStrategy()

    target_setl = next((s for s in dataset.settlements if "scen_010" in s.id), None)
    assert target_setl is not None

    res = rel_strategy.retrieve(case_id="TEST-10", settlement_id=target_setl.id, target_variance=1500000, dataset=dataset)

    # There are no refunds, disputes, or adjustments in this settlement
    deduction_cands = [c for c in res.candidates if c.entity_type in ("refund", "dispute", "adjustment")]
    assert len(deduction_cands) == 0


def test_upi_event_history_retrieval(retrieval_test_env):
    """Test 9: UPI Event retrieval extracts complete chronological history and transitions."""
    dataset = retrieval_test_env["dataset"]
    upi_strategy = UPIEventRetrievalStrategy()

    target_setl = next((s for s in dataset.settlements if "scen_005" in s.id), None)
    assert target_setl is not None

    res = upi_strategy.retrieve(case_id="TEST-05", settlement_id=target_setl.id, target_variance=0, dataset=dataset)

    assert res.strategy == RetrievalStrategy.UPI_EVENT
    assert len(res.candidates) >= 4  # 1 transaction + 3 events

    upi_txns = [c for c in res.candidates if c.entity_type == "upi_transaction"]
    upi_events = [c for c in res.candidates if c.entity_type == "upi_event"]

    assert len(upi_txns) == 1
    assert len(upi_events) >= 3

    # Check reconstructed determined status in metadata
    txn_meta = upi_txns[0].evidence_metadata
    assert txn_meta["determined_status"] == "LATE_SUCCESS"
    assert "event_history" in txn_meta
    assert len(txn_meta["event_history"]) == 3


def test_typed_provenance_verification(retrieval_test_env):
    """Test 10 & 11: Typed provenance verifies complete cell coordinates and flags incomplete records."""
    dataset = retrieval_test_env["dataset"]
    prov_strategy = TypedProvenanceRetrievalStrategy()

    target_setl = dataset.settlements[0]
    res = prov_strategy.retrieve(case_id="TEST-PROV", settlement_id=target_setl.id, target_variance=0, dataset=dataset)

    assert len(res.candidates) > 0
    for c in res.candidates:
        assert c.is_provenance_complete is True
        assert c.evidence_metadata["provenance_status"] == "VERIFIED"
        assert c.provenance is not None
        assert len(c.provenance.source_hash) == 64
        assert len(c.provenance.record_hash) == 64


def test_benchmark_runner_full_matrix(retrieval_test_env):
    """Test 12, 13, 14: Run full benchmark matrix (6 strategies x 10 scenarios) and export JSON/CSV."""
    dataset = retrieval_test_env["dataset"]
    gt_path = retrieval_test_env["gt_path"]
    exp_dir = retrieval_test_env["exp_dir"]

    runner = RetrievalBenchmarkRunner()
    report = runner.run_all_experiments(dataset, gt_path, export_dir=exp_dir)

    assert report.total_experiments_run == 60  # 6 strategies * 10 scenarios
    assert len(report.strategies_evaluated) == 6
    assert len(report.strategy_metrics) == 6

    # Verify exported files exist
    assert (Path(exp_dir) / "results.json").exists()
    assert (Path(exp_dir) / "results.csv").exists()

    # Compare Recall and Decoy Rejection across strategies:
    # ATTRIBUTE has high recall but low decoy rejection
    attr_metrics = report.strategy_metrics["ATTRIBUTE"]
    assert attr_metrics.decoy_rejection_rate_pct < 50.0  # Captures decoys

    # RELATIONSHIP rejects unrelated payment and settlement decoys (e.g. VAR-002, VAR-009)
    rel_metrics = report.strategy_metrics["RELATIONSHIP"]
    assert rel_metrics.decoy_rejection_rate_pct >= 75.0  # Rejects relational decoys

    # TEMPORAL_RELATIONSHIP rejects wrong-date decoys as well
    temp_metrics = report.strategy_metrics["TEMPORAL_RELATIONSHIP"]
    assert temp_metrics.decoy_rejection_rate_pct >= 75.0
