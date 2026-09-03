from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.agentic_investigation.models import AgentRoundResponse, ToolRequest, ToolResult
from neofinesse.ai_investigation.evidence_pack import EvidenceItem
from neofinesse.ai_investigation.models import ConflictItem
from neofinesse.investigation.models import Hypothesis, InvestigationStatus


class InvestigationRoundRecord(BaseModel):
    """Snapshot of a single investigation round for full deterministic replayability."""

    model_config = ConfigDict(extra="forbid")

    round_number: int
    evidence_ids_available: List[str]
    agent_response: Optional[AgentRoundResponse] = None
    tool_requests: List[ToolRequest] = Field(default_factory=list)
    tool_results: List[ToolResult] = Field(default_factory=list)
    verified_hypotheses: List[Hypothesis] = Field(default_factory=list)
    rejected_reasons: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


class InvestigationState(BaseModel):
    """Comprehensive, serializable multi-round state preserving full investigative history."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    settlement_id: str
    target_variance: int  # in paise
    task_category: str
    round_number: int = 1
    current_evidence: Dict[str, EvidenceItem] = Field(default_factory=dict)
    evidence_history: List[EvidenceItem] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    rejected_hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    completed_requests: List[ToolRequest] = Field(default_factory=list)
    tool_results: List[ToolResult] = Field(default_factory=list)
    conflicts: List[ConflictItem] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    rounds: List[InvestigationRoundRecord] = Field(default_factory=list)
    final_status: Optional[InvestigationStatus] = None
    winning_hypothesis: Optional[Hypothesis] = None

    def add_evidence(self, items: List[EvidenceItem]) -> List[str]:
        """Adds new evidence items to state, deduplicating by canonical identity."""
        added_ids: List[str] = []
        for item in items:
            if item.evidence_id not in self.current_evidence:
                self.current_evidence[item.evidence_id] = item
                self.evidence_history.append(item)
                added_ids.append(item.evidence_id)
        return added_ids

    def record_round_snapshot(
        self,
        round_number: int,
        agent_response: Optional[AgentRoundResponse],
        tool_requests: List[ToolRequest],
        tool_results: List[ToolResult],
        verified_hypotheses: List[Hypothesis],
        rejected_reasons: List[Dict[str, Any]],
    ) -> InvestigationRoundRecord:
        """Appends an immutable round record to the investigation state."""
        record = InvestigationRoundRecord(
            round_number=round_number,
            evidence_ids_available=list(self.current_evidence.keys()),
            agent_response=agent_response,
            tool_requests=tool_requests,
            tool_results=tool_results,
            verified_hypotheses=verified_hypotheses,
            rejected_reasons=rejected_reasons,
            timestamp=datetime.now(),
        )
        self.rounds.append(record)
        return record
