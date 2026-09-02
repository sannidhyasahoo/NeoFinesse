from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.models.settlement import Settlement
from neofinesse.retrieval.base import EvidenceCandidate, InvestigationTaskCategory, RetrievalResult


class EvidenceItem(BaseModel):
    """Clean, self-contained provenance-backed evidence unit sent to LLM."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(description="Unique deterministic evidence reference ID (e.g. EV-1, EV-2)")
    candidate_id: str
    entity_id: str
    entity_type: str
    amount_paise: int
    amount_inr: float
    net_financial_effect_paise: int
    net_financial_effect_inr: float
    timestamp_iso: Optional[str] = None
    status: Optional[str] = None
    relationship_path: str
    source_id: str
    source_file: str
    source_sheet: Optional[str] = None
    source_row: int
    source_hash: str
    record_hash: str
    evidence_metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidencePack(BaseModel):
    """Structured, minimal evidence pack providing only relevant context to the LLM."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    settlement_id: str
    target_variance_paise: int
    target_variance_inr: float
    task_category: str
    settlement_context: Optional[Dict[str, Any]] = None
    settlement_lines: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)
    total_evidence_count: int = 0


class EvidencePackBuilder:
    """Constructs isolated, verifiable evidence packs from dataset and retrieval results."""

    @staticmethod
    def build_pack(
        case_id: str,
        settlement_id: str,
        target_variance: int,
        dataset: IngestedDataset,
        retrieval_result: RetrievalResult,
        task_category: InvestigationTaskCategory = InvestigationTaskCategory.SETTLEMENT_RCA,
    ) -> EvidencePack:
        # 1. Target settlement context
        settlement: Optional[Settlement] = next((s for s in dataset.settlements if s.id == settlement_id), None)
        setl_ctx: Optional[Dict[str, Any]] = None
        setl_lines_summary: List[Dict[str, Any]] = []

        if settlement:
            setl_ctx = {
                "settlement_id": settlement.id,
                "amount_paise": settlement.amount,
                "amount_inr": settlement.amount / 100.0,
                "gross_amount_paise": settlement.gross_amount,
                "gross_amount_inr": (settlement.gross_amount or 0) / 100.0,
                "fee_paise": settlement.fees,
                "tax_paise": settlement.tax,
                "utr": settlement.utr,
                "status": settlement.status.value if hasattr(settlement.status, "value") else str(settlement.status),
                "recon_status": settlement.recon_status.value if hasattr(settlement.recon_status, "value") else str(settlement.recon_status),
                "created_at": settlement.created_at.isoformat() if settlement.created_at else None,
                "settled_at": settlement.settled_at.isoformat() if settlement.settled_at else None,
            }

            # Add constituent settlement lines
            target_lines = [l for l in dataset.settlement_lines if l.settlement_id == settlement_id]
            for l in target_lines:
                setl_lines_summary.append(
                    {
                        "settlement_line_id": l.settlement_line_id,
                        "source_event_type": l.source_event_type.value,
                        "source_event_id": l.source_event_id,
                        "amount_paise": l.amount,
                        "amount_inr": l.amount / 100.0,
                        "net_amount_paise": l.net_amount,
                        "fee_paise": l.fee,
                        "tax_paise": l.tax,
                        "event_timestamp": l.event_timestamp.isoformat() if l.event_timestamp else None,
                    }
                )

        # 2. Map candidates into EvidenceItems with deterministic EV-N IDs
        evidence_items: List[EvidenceItem] = []
        for idx, c in enumerate(retrieval_result.candidates):
            ev_id = f"EV-{idx+1}"
            prov = c.provenance

            # Extract source information safely
            source_id = prov.source_id if prov else "UNKNOWN_SRC"
            source_file = prov.source_file if prov else "unknown_file"
            source_sheet = prov.source_sheet if prov else None
            source_row = prov.source_row if prov else 0
            source_hash = prov.source_hash if prov else "MISSING_HASH"
            record_hash = prov.record_hash if prov else "MISSING_HASH"

            # Status from metadata or candidate
            status = c.evidence_metadata.get("status")

            evidence_items.append(
                EvidenceItem(
                    evidence_id=ev_id,
                    candidate_id=c.candidate_id,
                    entity_id=c.entity_id,
                    entity_type=c.entity_type,
                    amount_paise=c.amount,
                    amount_inr=c.amount / 100.0,
                    net_financial_effect_paise=c.net_financial_effect,
                    net_financial_effect_inr=c.net_financial_effect / 100.0,
                    timestamp_iso=c.timestamp.isoformat() if c.timestamp else None,
                    status=str(status) if status else None,
                    relationship_path=c.relationship_path,
                    source_id=source_id,
                    source_file=source_file,
                    source_sheet=source_sheet,
                    source_row=source_row,
                    source_hash=source_hash,
                    record_hash=record_hash,
                    evidence_metadata=c.evidence_metadata,
                )
            )

        return EvidencePack(
            case_id=case_id,
            settlement_id=settlement_id,
            target_variance_paise=target_variance,
            target_variance_inr=target_variance / 100.0,
            task_category=task_category.value,
            settlement_context=setl_ctx,
            settlement_lines=setl_lines_summary,
            evidence_items=evidence_items,
            retrieval_metadata=retrieval_result.retrieval_metadata,
            total_evidence_count=len(evidence_items),
        )
