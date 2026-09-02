from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from neofinesse.ingestion.parser import RawRecord
from neofinesse.models.base import ProvenanceReference


class ValidationIssue(BaseModel):
    category: str = Field(description="SCHEMA, FINANCIAL, IDENTITY, TEMPORAL, PROVENANCE")
    field: Optional[str] = Field(default=None)
    message: str = Field(description="Description of validation issue")
    severity: str = Field(default="ERROR", description="ERROR or WARNING")
    source_reference: Optional[str] = Field(default=None)


class ValidationResult(BaseModel):
    is_valid: bool = True
    issues: List[ValidationIssue] = Field(default_factory=list)


class DataValidator:
    """Validates raw records for schema, financial, identity, temporal, and provenance compliance."""

    def __init__(self):
        self.seen_ids: Set[str] = set()

    def validate_record(self, record: RawRecord, entity_type: str, required_fields: List[str]) -> ValidationResult:
        result = ValidationResult()
        data = record.data
        prov = record.provenance
        ref_str = f"{prov.source_file}:{prov.source_sheet or ''}:Row_{prov.source_row}"

        # 1. Provenance Validation
        if not prov.source_file or not prov.source_hash or not prov.record_hash or prov.source_row < 1:
            result.is_valid = False
            result.issues.append(
                ValidationIssue(
                    category="PROVENANCE",
                    message="Incomplete or invalid provenance reference.",
                    source_reference=ref_str,
                )
            )

        # 2. Schema Validation (Required Fields)
        for req in required_fields:
            if req not in data or data[req] is None or (isinstance(data[req], str) and data[req].strip() == ""):
                result.is_valid = False
                result.issues.append(
                    ValidationIssue(
                        category="SCHEMA",
                        field=req,
                        message=f"Missing required field: {req}",
                        source_reference=ref_str,
                    )
                )

        # 3. Financial Validation (Paise Integers)
        amount_fields = ["amount", "fee", "tax", "net_amount", "credit_amount", "debit_amount", "expected_amount", "variance"]
        for amt_field in amount_fields:
            if amt_field in data and data[amt_field] not in (None, ""):
                val = data[amt_field]
                try:
                    if isinstance(val, str) and "." in val:
                        result.is_valid = False
                        result.issues.append(
                            ValidationIssue(
                                category="FINANCIAL",
                                field=amt_field,
                                message=f"Floating-point string '{val}' found in monetary field {amt_field}; must be integer paise.",
                                source_reference=ref_str,
                            )
                        )
                    else:
                        int_val = int(val)
                except (ValueError, TypeError):
                    result.is_valid = False
                    result.issues.append(
                        ValidationIssue(
                            category="FINANCIAL",
                            field=amt_field,
                            message=f"Invalid monetary integer value '{val}' for field {amt_field}.",
                            source_reference=ref_str,
                        )
                    )

        # 4. Identity Validation (Unique Primary IDs)
        id_field_map = {
            "order": "id",
            "payment": "id",
            "upi_transaction": "upi_transaction_id",
            "upi_event": "event_id",
            "refund": "id",
            "dispute": "id",
            "adjustment": "id",
            "transfer": "id",
            "settlement_line": "settlement_line_id",
            "settlement": "id",
            "bank_transaction": "bank_txn_id",
            "settlement_line_xlsx": "Line ID",
            "bank_statement_xlsx": "Txn ID",
        }
        id_field = id_field_map.get(entity_type, "id")
        if id_field in data and data[id_field] not in (None, ""):
            eid = f"{entity_type}:{data[id_field]}"
            if eid in self.seen_ids:
                result.is_valid = False
                result.issues.append(
                    ValidationIssue(
                        category="IDENTITY",
                        field=id_field,
                        message=f"Duplicate entity ID detected: {data[id_field]} for entity type {entity_type}",
                        source_reference=ref_str,
                    )
                )
            else:
                self.seen_ids.add(eid)

        # 5. Temporal Validation
        time_fields = ["created_at", "captured_at", "processed_at", "initiated_at", "timestamp", "settled_at", "value_date"]
        for tf in time_fields:
            if tf in data and data[tf] not in (None, ""):
                t_val = str(data[tf])
                try:
                    datetime.fromisoformat(t_val)
                except ValueError:
                    result.is_valid = False
                    result.issues.append(
                        ValidationIssue(
                            category="TEMPORAL",
                            field=tf,
                            message=f"Invalid ISO timestamp format: '{t_val}'",
                            source_reference=ref_str,
                        )
                    )

        return result
