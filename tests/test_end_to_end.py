from pathlib import Path
import pytest

from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestionPipeline


def test_full_pipeline_end_to_end(tmp_path):
    """Test 12: Full workflow: generate -> export -> ingest -> validate -> verify domain objects."""
    data_dir = tmp_path / "data"
    gt_dir = tmp_path / "ground_truth"

    config = GeneratorConfig(
        seed=101,
        num_orders=100,
        num_payments=100,
        num_settlements=8,
        num_refunds=10,
        num_disputes=5,
        num_adjustments=5,
        num_transfers=3,
        output_dir=str(data_dir),
        ground_truth_dir=str(gt_dir),
    )

    # 1. Generate
    world = FinancialDataGenerator(config).generate()
    assert len(world.orders) >= 100
    assert len(world.ground_truths) == 10

    # 2. Export
    exporter = DataExporter(world, config)
    export_meta = exporter.export_all()

    assert Path(export_meta["ground_truth_path"]).exists()
    assert (data_dir / "payments.csv").exists()
    assert (data_dir / "settlement_lines.csv").exists()
    assert (data_dir / "settlements.csv").exists()
    assert (data_dir / "settlement_recon.xlsx").exists()
    assert (data_dir / "bank_statement.xlsx").exists()
    assert (data_dir / "source_registry.json").exists()

    # 3. Ingest & Validate
    pipeline = IngestionPipeline(data_dir=str(data_dir))
    dataset = pipeline.run()

    # Verify zero validation errors on clean synthetic data
    assert len(dataset.validation_errors) == 0, f"Validation errors: {dataset.validation_errors}"

    # Verify populated domain objects
    assert len(dataset.orders) > 0
    assert len(dataset.payments) > 0
    assert len(dataset.settlement_lines) > 0
    assert len(dataset.settlements) > 0
    assert len(dataset.bank_transactions) > 0

    # 4. Inspect normalized objects & provenance
    sample_payment = dataset.payments[0]
    assert sample_payment.amount > 0
    assert isinstance(sample_payment.amount, int)
    assert sample_payment.provenance is not None
    assert sample_payment.provenance.source_file == "payments.csv"
    assert sample_payment.provenance.source_row >= 2
    assert sample_payment.provenance.source_columns is not None
    assert len(sample_payment.provenance.source_hash) == 64
    assert len(sample_payment.provenance.record_hash) == 64

    # Verify SettlementLine composition
    sample_line = dataset.settlement_lines[0]
    assert sample_line.settlement_id is not None
    assert sample_line.net_amount is not None
    assert sample_line.provenance.source_file == "settlement_lines.csv"
