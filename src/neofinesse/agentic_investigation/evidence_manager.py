from typing import Dict, List, Optional

from neofinesse.agentic_investigation.models import ToolResult
from neofinesse.agentic_investigation.state import InvestigationState
from neofinesse.ai_investigation.evidence_pack import EvidenceItem, EvidencePack, EvidencePackBuilder
from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.retrieval.base import InvestigationTaskCategory, RetrievalResult


class AgentEvidenceManager:
    """Manages accumulation, deduplication, and packaging of evidence across investigation rounds."""

    @staticmethod
    def initialize_evidence(
        state: InvestigationState,
        dataset: IngestedDataset,
        retrieval_result: RetrievalResult,
        task_category: InvestigationTaskCategory,
    ) -> EvidencePack:
        """Constructs the initial round 1 EvidencePack from Phase 4 retrieval."""
        initial_pack = EvidencePackBuilder.build_pack(
            case_id=state.case_id,
            settlement_id=state.settlement_id,
            target_variance=state.target_variance,
            dataset=dataset,
            retrieval_result=retrieval_result,
            task_category=task_category,
        )

        # Store in state
        state.add_evidence(initial_pack.evidence_items)
        return initial_pack

    @staticmethod
    def merge_tool_evidence(
        state: InvestigationState,
        tool_results: List[ToolResult],
    ) -> List[str]:
        """Merges new evidence items returned by tool executions into state."""
        all_new_items: List[EvidenceItem] = []
        for tr in tool_results:
            if tr.success and tr.evidence_items:
                all_new_items.extend(tr.evidence_items)

        return state.add_evidence(all_new_items)

    @staticmethod
    def build_round_evidence_pack(
        state: InvestigationState,
        dataset: IngestedDataset,
    ) -> EvidencePack:
        """Constructs updated EvidencePack for the current round from cumulative state."""
        settlement = next((s for s in dataset.settlements if s.id == state.settlement_id), None)
        setl_ctx = None
        setl_lines = []

        if settlement:
            setl_ctx = {
                "settlement_id": settlement.id,
                "amount_paise": settlement.amount,
                "amount_inr": settlement.amount / 100.0,
                "gross_amount_paise": settlement.gross_amount,
                "gross_amount_inr": (settlement.gross_amount or 0) / 100.0,
                "fees": settlement.fees,
                "tax": settlement.tax,
                "utr": settlement.utr,
                "status": settlement.status.value if hasattr(settlement.status, "value") else str(settlement.status),
                "recon_status": settlement.recon_status.value if hasattr(settlement.recon_status, "value") else str(settlement.recon_status),
                "created_at": settlement.created_at.isoformat() if settlement.created_at else None,
                "settled_at": settlement.settled_at.isoformat() if settlement.settled_at else None,
            }
            target_lines = [l for l in dataset.settlement_lines if l.settlement_id == state.settlement_id]
            for l in target_lines:
                setl_lines.append(
                    {
                        "settlement_line_id": l.settlement_line_id,
                        "source_event_type": l.source_event_type.value,
                        "source_event_id": l.source_event_id,
                        "amount_paise": l.amount,
                        "amount_inr": l.amount / 100.0,
                        "net_amount_paise": l.net_amount,
                    }
                )

        # Cumulative evidence list
        evidence_list = list(state.current_evidence.values())

        # Include prior tool results in metadata
        tool_history = [
            {
                "tool": tr.tool,
                "success": tr.success,
                "output": tr.output,
                "error": tr.error,
            }
            for tr in state.tool_results
        ]

        return EvidencePack(
            case_id=state.case_id,
            settlement_id=state.settlement_id,
            target_variance_paise=state.target_variance,
            target_variance_inr=state.target_variance / 100.0,
            task_category=state.task_category,
            settlement_context=setl_ctx,
            settlement_lines=setl_lines,
            evidence_items=evidence_list,
            retrieval_metadata={"tool_execution_history": tool_history, "round": state.round_number},
            total_evidence_count=len(evidence_list),
        )
