import shutil
from pathlib import Path
import pytest

from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.parser import FileParser, col_index_to_letter
from neofinesse.ingestion.pipeline import IngestionPipeline
from neofinesse.ingestion.registry import SourceRegistry


@pytest.fixture
def generated_dataset(tmp_path):
    data_dir = tmp_path / "data"
    gt_dir = tmp_path / "ground_truth"
    config = GeneratorConfig(seed=42, num_orders=60, num_settlements=6, output_dir=str(data_dir), ground_truth_dir=str(gt_dir))

    world = FinancialDataGenerator(config).generate()
    exporter = DataExporter(world, config)
    res = exporter.export_all()

    return {"data_dir": str(data_dir), "gt_dir": str(gt_dir), "world": world}


def test_col_index_to_letter():
    assert col_index_to_letter(0) == "A"
    assert col_index_to_letter(1) == "B"
    assert col_index_to_letter(25) == "Z"
    assert col_index_to_letter(26) == "AA"
    assert col_index_to_letter(27) == "AB"


def test_file_hashing_deterministic(generated_dataset):
    """Test 8: File hashes are deterministic for identical files."""
    data_dir = Path(generated_dataset["data_dir"])
    registry = SourceRegistry(str(data_dir))

    entries = registry.discover_and_register_files()
    assert len(entries) >= 10

    # Recompute file hashes
    for filename, entry in entries.items():
        recomputed = registry.compute_file_hash(Path(entry.file_path))
        assert entry.file_hash == recomputed
        assert len(entry.file_hash) == 64  # SHA-256 hex length


def test_record_hashing_tamper_detection():
    """Test 9: Record hashes change when record contents change."""
    parser = FileParser()
    row1 = {"id": "pay_001", "amount": 10000, "status": "captured"}
    row2 = {"id": "pay_001", "amount": 10000, "status": "captured"}
    row3 = {"id": "pay_001", "amount": 10001, "status": "captured"}  # Tampered amount

    hash1 = parser.compute_record_hash(row1)
    hash2 = parser.compute_record_hash(row2)
    hash3 = parser.compute_record_hash(row3)

    assert hash1 == hash2
    assert hash1 != hash3


def test_ingestion_provenance_preservation(generated_dataset):
    """Test 10: Ingested records preserve complete provenance."""
    pipeline = IngestionPipeline(data_dir=generated_dataset["data_dir"])
    dataset = pipeline.run()

    assert len(dataset.payments) > 0
    for p in dataset.payments:
        assert p.provenance is not None
        assert p.provenance.source_file == "payments.csv"
        assert p.provenance.source_row >= 2
        assert p.provenance.source_columns is not None
        assert "amount" in p.provenance.source_columns
        assert len(p.provenance.source_hash) == 64
        assert len(p.provenance.record_hash) == 64

    assert len(dataset.settlement_lines) > 0
    for sl in dataset.settlement_lines:
        assert sl.provenance is not None
        assert sl.provenance.source_file == "settlement_lines.csv"
        assert sl.provenance.source_row >= 2


def test_ground_truth_isolation(generated_dataset):
    """Test 11: Ground truth is not loaded by the ingestion pipeline."""
    pipeline = IngestionPipeline(data_dir=generated_dataset["data_dir"])
    dataset = pipeline.run()

    # Ground truth files/records should not exist in IngestedDataset
    assert not hasattr(dataset, "ground_truths")
    for filename in dataset.registry:
        assert "ground_truth" not in filename
