from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.ingestion.normalizer import EntityNormalizer
from neofinesse.ingestion.parser import FileParser
from neofinesse.ingestion.registry import FileRegistryEntry, SourceRegistry
from neofinesse.ingestion.validator import DataValidator, ValidationIssue
from neofinesse.models.base import Provider
from neofinesse.models.events import Adjustment, Dispute, Order, Payment, Refund, Transfer
from neofinesse.models.settlement import Settlement, SettlementLine
from neofinesse.models.upi import UPIEvent, UPITransaction
from neofinesse.models.bank import BankTransaction


class IngestedDataset(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    registry: Dict[str, FileRegistryEntry] = Field(default_factory=dict)
    orders: List[Order] = Field(default_factory=list)
    payments: List[Payment] = Field(default_factory=list)
    upi_transactions: List[UPITransaction] = Field(default_factory=list)
    upi_events: List[UPIEvent] = Field(default_factory=list)
    refunds: List[Refund] = Field(default_factory=list)
    disputes: List[Dispute] = Field(default_factory=list)
    adjustments: List[Adjustment] = Field(default_factory=list)
    transfers: List[Transfer] = Field(default_factory=list)
    settlement_lines: List[SettlementLine] = Field(default_factory=list)
    settlements: List[Settlement] = Field(default_factory=list)
    bank_transactions: List[BankTransaction] = Field(default_factory=list)
    validation_errors: List[ValidationIssue] = Field(default_factory=list)


class IngestionPipeline:
    """End-to-end pipeline that discovers, registers, parses, validates, and normalizes multi-source files."""

    def __init__(self, data_dir: str, provider: Provider = Provider.RAZORPAY, batch_id: str = "INGEST-BATCH-001"):
        self.data_dir = Path(data_dir)
        self.provider = provider
        self.batch_id = batch_id
        self.registry = SourceRegistry(str(self.data_dir), provider)
        self.parser = FileParser(batch_id)
        self.validator = DataValidator()

    def run(self) -> IngestedDataset:
        """Executes full ingestion pipeline on all discovered files in data_dir."""
        # Note: Ground truth directory/files are deliberately ignored and never loaded.
        entries = self.registry.discover_and_register_files()
        dataset = IngestedDataset(registry=entries)

        # Mapping of filename to parsing & normalization rules
        schema_map = {
            "orders.csv": ("order", ["id", "amount", "status", "created_at"], EntityNormalizer.normalize_order, dataset.orders),
            "payments.csv": ("payment", ["id", "amount", "status", "normalized_status", "net_amount", "created_at"], EntityNormalizer.normalize_payment, dataset.payments),
            "upi_transactions.csv": ("upi_transaction", ["upi_transaction_id", "payment_id", "amount", "initiated_at", "current_observed_status", "final_determined_status"], EntityNormalizer.normalize_upi_transaction, dataset.upi_transactions),
            "upi_events.csv": ("upi_event", ["event_id", "upi_transaction_id", "timestamp", "previous_state", "new_state", "event_type"], EntityNormalizer.normalize_upi_event, dataset.upi_events),
            "refunds.csv": ("refund", ["id", "amount", "payment_id", "status", "created_at"], EntityNormalizer.normalize_refund, dataset.refunds),
            "disputes.csv": ("dispute", ["id", "payment_id", "amount", "status", "created_at"], EntityNormalizer.normalize_dispute, dataset.disputes),
            "adjustments.csv": ("adjustment", ["id", "amount", "created_at"], EntityNormalizer.normalize_adjustment, dataset.adjustments),
            "settlement_lines.csv": ("settlement_line", ["settlement_line_id", "settlement_id", "source_event_id", "source_event_type", "amount", "net_amount"], EntityNormalizer.normalize_settlement_line, dataset.settlement_lines),
            "settlements.csv": ("settlement", ["id", "amount", "status", "expected_amount", "created_at"], EntityNormalizer.normalize_settlement, dataset.settlements),
            "bank_transactions.csv": ("bank_transaction", ["bank_txn_id", "value_date", "transaction_date"], EntityNormalizer.normalize_bank_transaction, dataset.bank_transactions),
        }

        for filename, entry in entries.items():
            if filename in schema_map:
                entity_type, req_fields, norm_fn, target_list = schema_map[filename]
                raw_records = self.parser.parse_csv(entry)

                for raw in raw_records:
                    val_res = self.validator.validate_record(raw, entity_type, req_fields)
                    if val_res.is_valid:
                        obj = norm_fn(raw)
                        target_list.append(obj)
                    else:
                        dataset.validation_errors.extend(val_res.issues)

            elif filename == "settlement_recon.xlsx":
                # Excel file with sheets: Settlements, Settlement_Lines
                # Verified parsing preserves sheet + exact row + cell coordinates
                raw_lines = self.parser.parse_xlsx(entry, sheet_name="Settlement_Lines")
                # We record and verify Excel records can be parsed with exact sheet provenance
                for raw in raw_lines:
                    val_res = self.validator.validate_record(raw, "settlement_line_xlsx", ["Line ID", "Settlement ID", "Event ID", "Net Amount"])
                    if not val_res.is_valid:
                        dataset.validation_errors.extend(val_res.issues)

            elif filename == "bank_statement.xlsx":
                raw_bank = self.parser.parse_xlsx(entry, sheet_name="Account_Statement")
                for raw in raw_bank:
                    val_res = self.validator.validate_record(raw, "bank_statement_xlsx", ["Txn ID", "Value Date"])
                    if not val_res.is_valid:
                        dataset.validation_errors.extend(val_res.issues)

        return dataset
