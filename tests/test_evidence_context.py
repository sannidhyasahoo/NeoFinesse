"""
tests/test_evidence_context.py
==============================
Comprehensive unit and integration tests for EvidenceContextService:
- Exact cell context extraction and row alignment
- Real source value verification for F31 (Row 31, Col F -> 4000.0 / INR 4,000)
- Boundary window clamping and multi-row context
- Rejection of directory traversal and unknown sources
- Multi-sheet XLSX parsing and CSV parsing
- Cryptographic provenance and SHA-256 integrity
"""
from pathlib import Path
import pytest

from neofinesse.services.evidence_context_service import (
    EvidenceContextService,
    column_letter_to_index,
    index_to_column_letter,
    parse_cell_address,
)


@pytest.fixture
def dataset_dir() -> Path:
    base_dir = Path(__file__).parent.parent / "data" / "demo_dataset"
    return base_dir


@pytest.fixture
def context_service(dataset_dir: Path) -> EvidenceContextService:
    return EvidenceContextService(dataset_dir)


# =============================================================================
# 1. Address Parsing & Column Conversion Tests
# =============================================================================

def test_column_letter_to_index():
    assert column_letter_to_index("A") == 1
    assert column_letter_to_index("B") == 2
    assert column_letter_to_index("F") == 6
    assert column_letter_to_index("H") == 8
    assert column_letter_to_index("Z") == 26
    assert column_letter_to_index("AA") == 27
    assert column_letter_to_index("AZ") == 52
    with pytest.raises(ValueError):
        column_letter_to_index("123")


def test_index_to_column_letter():
    assert index_to_column_letter(1) == "A"
    assert index_to_column_letter(2) == "B"
    assert index_to_column_letter(6) == "F"
    assert index_to_column_letter(8) == "H"
    assert index_to_column_letter(26) == "Z"
    assert index_to_column_letter(27) == "AA"
    assert index_to_column_letter(52) == "AZ"
    with pytest.raises(ValueError):
        index_to_column_letter(0)


def test_parse_cell_address():
    # Simple address
    sheet, col_letter, col_idx, row_idx = parse_cell_address("F31")
    assert sheet is None
    assert col_letter == "F"
    assert col_idx == 6
    assert row_idx == 31

    # Sheet + address
    sheet, col_letter, col_idx, row_idx = parse_cell_address("Refunds_FY24_Archive!F31")
    assert sheet == "Refunds_FY24_Archive"
    assert col_letter == "F"
    assert col_idx == 6
    assert row_idx == 31

    # Quoted sheet name
    sheet, col_letter, col_idx, row_idx = parse_cell_address("'Account Statement'!C19")
    assert sheet == "Account Statement"
    assert col_letter == "C"
    assert col_idx == 3
    assert row_idx == 19

    with pytest.raises(ValueError):
        parse_cell_address("INVALID_CELL_123!!")


# =============================================================================
# 2. Specific Requirements Tests (Tests 1-11)
# =============================================================================

def test_1_f31_request_returns_non_empty_rows(context_service: EvidenceContextService):
    """Test 1: Request refunds.csv Refunds_FY24_Archive F31 -> rows.length > 0 and target cell exists."""
    result = context_service.get_cell_context(
        filename="refunds.csv",
        sheet="Refunds_FY24_Archive",
        cell="F31",
        row_radius=3,
        column_radius=3,
    )
    assert result["status"] == "SUCCESS"
    rows = result["context"]["rows"]
    assert len(rows) > 0
    assert any(r["is_target_row"] for r in rows)


def test_2_f31_target_value_equals_actual_source_value(context_service: EvidenceContextService):
    """Test 2: Assert target_cell == F31 and returned value equals actual source value (4000.0)."""
    result = context_service.get_cell_context(
        filename="refunds.csv",
        sheet="Refunds_FY24_Archive",
        cell="F31",
        row_radius=3,
        column_radius=3,
    )
    assert result["target_cell"] == "F31"
    assert result["target_row"] == 31
    assert result["target_column"] == 6
    # Source row 31 has amount 4000.00 / 400000
    assert result["target_value"] in (4000.0, 4000, 400000, "4000.00")


def test_3_surrounding_rows_returned(context_service: EvidenceContextService):
    """Test 3: Assert surrounding rows (rows 28-34) are returned for F31 with radius 3."""
    result = context_service.get_cell_context(
        filename="refunds.csv",
        cell="F31",
        row_radius=3,
        column_radius=3,
    )
    rows = result["context"]["rows"]
    row_numbers = [r["row_number"] for r in rows]
    assert 28 in row_numbers
    assert 31 in row_numbers
    assert 34 in row_numbers
    assert len(rows) == 7


def test_4_target_cell_has_is_target_true(context_service: EvidenceContextService):
    """Test 4: Assert target cell has is_target == true and only target cell has is_target == true."""
    result = context_service.get_cell_context(
        filename="refunds.csv",
        cell="F31",
        row_radius=3,
        column_radius=3,
    )
    target_count = 0
    for r in result["context"]["rows"]:
        for c in r["cells"]:
            if c["address"] == "F31":
                assert c["is_target"] is True
                target_count += 1
            else:
                assert c["is_target"] is False
    assert target_count == 1


def test_5_first_and_last_row_boundaries(context_service: EvidenceContextService):
    """Test 5: Test first/last row boundaries clamp cleanly."""
    # First row (Row 1)
    res_first = context_service.get_cell_context(filename="refunds.csv", cell="A1", row_radius=3)
    assert res_first["window"]["min_row"] == 1
    assert res_first["context"]["rows"][0]["row_number"] == 1

    # Last row
    total_rows = res_first["total_rows"]
    res_last = context_service.get_cell_context(filename="refunds.csv", row=total_rows, column=1, row_radius=3)
    assert res_last["window"]["max_row"] == total_rows
    assert res_last["context"]["rows"][-1]["row_number"] == total_rows


def test_6_invalid_cell_address_raises(context_service: EvidenceContextService):
    """Test 6: Test invalid cell address raises ValueError."""
    with pytest.raises(ValueError):
        context_service.get_cell_context(filename="refunds.csv", cell="NOT_A_VALID_CELL!!")


def test_7_invalid_sheet_name_raises(context_service: EvidenceContextService):
    """Test 7: Test invalid sheet name raises ValueError."""
    with pytest.raises(ValueError, match="not found in"):
        context_service.get_cell_context(
            filename="settlement_recon.xlsx",
            sheet="NonExistentSheet_9999",
            cell="A1",
        )


def test_8_unknown_source_raises(context_service: EvidenceContextService):
    """Test 8: Test unknown source file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="not found in source registry"):
        context_service.get_cell_context(filename="unregistered_phantom_file.csv", cell="A1")


def test_9_csv_parsing(context_service: EvidenceContextService):
    """Test 9: Test CSV context extraction."""
    result = context_service.get_cell_context(filename="settlements.csv", cell="B2")
    assert result["status"] == "SUCCESS"
    assert result["source_file"] == "settlements.csv"
    assert result["target_cell"] == "B2"
    assert len(result["context"]["rows"]) > 0


def test_10_xlsx_parsing(context_service: EvidenceContextService):
    """Test 10: Test XLSX context extraction with sheets."""
    result = context_service.get_cell_context(
        filename="settlement_recon.xlsx",
        sheet="Settlements",
        cell="A2",
    )
    assert result["status"] == "SUCCESS"
    assert result["source_file"] == "settlement_recon.xlsx"
    assert result["sheet"] == "Settlements"
    assert result["target_cell"] == "A2"
    assert len(result["context"]["rows"]) > 0


def test_11_sha256_provenance_metadata_preserved(context_service: EvidenceContextService):
    """Test 11: Test that existing SHA-256/provenance metadata remains valid and consistent."""
    result = context_service.get_cell_context(filename="refunds.csv", cell="F31")
    assert result["is_provenance_verified"] is True
    assert len(result["file_hash"]) == 64
    assert len(result["record_hash"]) == 64
    # Re-running computes identical deterministic hashes
    result_repeat = context_service.get_cell_context(filename="refunds.csv", cell="F31")
    assert result["file_hash"] == result_repeat["file_hash"]
    assert result["record_hash"] == result_repeat["record_hash"]


# =============================================================================
# 3. Security & Anti-Traversal Tests
# =============================================================================

def test_security_directory_traversal_prohibited(context_service: EvidenceContextService):
    with pytest.raises(PermissionError, match="Directory traversal prohibited"):
        context_service.get_cell_context(filename="../../secret.txt", cell="A1")

    with pytest.raises(PermissionError, match="Directory traversal prohibited"):
        context_service.get_cell_context(filename="../demo_dataset/payments.csv", cell="A1")

    with pytest.raises(PermissionError, match="Directory traversal prohibited"):
        context_service.get_cell_context(filename="sub/file.csv", cell="A1")
