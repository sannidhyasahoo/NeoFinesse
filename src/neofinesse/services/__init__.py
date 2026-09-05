"""
neofinesse.services
Service layer for dataset generation, file export, batch ingestion, and analysis execution.
"""
from neofinesse.services.dataset_service import DatasetService, generate_demo_dataset, analyze_dataset_directory
from neofinesse.services.evidence_context_service import (
    EvidenceContextService,
    column_letter_to_index,
    index_to_column_letter,
    parse_cell_address,
)
from neofinesse.services.escalation_summary_service import (
    EscalationSummaryService,
    HumanReviewHandoff,
    InvestigationStep,
    MissingEvidenceItem,
    MissingEvidenceCategory,
)

__all__ = [
    "DatasetService",
    "generate_demo_dataset",
    "analyze_dataset_directory",
    "EvidenceContextService",
    "column_letter_to_index",
    "index_to_column_letter",
    "parse_cell_address",
    "EscalationSummaryService",
    "HumanReviewHandoff",
    "InvestigationStep",
    "MissingEvidenceItem",
    "MissingEvidenceCategory",
]
