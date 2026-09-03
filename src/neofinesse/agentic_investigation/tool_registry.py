from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from neofinesse.agentic_investigation.models import ToolRequest, ToolResult
from neofinesse.agentic_investigation.tools import InvestigationTools
from neofinesse.ingestion.pipeline import IngestedDataset


@dataclass
class ToolDefinition:
    name: str
    description: str
    required_arguments: List[str]
    argument_schema: Dict[str, Any]
    handler: Callable[..., ToolResult]


class ToolRegistry:
    """Typed registry for controlled agentic investigation tools."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        self.register_tool(
            ToolDefinition(
                name="retrieve_related_evidence",
                description="Retrieve evidence directly connected to a known entity (e.g. payment, settlement_line, refund, adjustment).",
                required_arguments=["entity_type", "entity_id", "relationship"],
                argument_schema={
                    "entity_type": "string (settlement_line, payment, refund, adjustment, dispute)",
                    "entity_id": "string ID of the entity",
                    "relationship": "string relationship path (e.g. source_event, payment_id)",
                },
                handler=InvestigationTools.retrieve_related_evidence,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="verify_membership",
                description="Verify whether a candidate event is a constituent member of a specific settlement batch.",
                required_arguments=["event_id", "settlement_id"],
                argument_schema={
                    "event_id": "string ID of the event or deduction (e.g. ADJ-123, RFND-456)",
                    "settlement_id": "string ID of the settlement batch",
                },
                handler=InvestigationTools.verify_membership,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="retrieve_upi_history",
                description="Retrieve complete chronological state transitions, timeout responses, and debit/reversal history for a UPI transaction.",
                required_arguments=["upi_transaction_id"],
                argument_schema={
                    "upi_transaction_id": "string ID of the UPI transaction",
                },
                handler=InvestigationTools.retrieve_upi_history,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="retrieve_temporal_neighbors",
                description="Retrieve candidate events within a bounded time window around a reference timestamp.",
                required_arguments=["entity_id", "reference_timestamp", "window_before_minutes", "window_after_minutes"],
                argument_schema={
                    "entity_id": "string reference entity ID",
                    "reference_timestamp": "ISO 8601 timestamp",
                    "window_before_minutes": "integer minutes before (max 180)",
                    "window_after_minutes": "integer minutes after (max 180)",
                },
                handler=InvestigationTools.retrieve_temporal_neighbors,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="retrieve_source_record",
                description="Inspect exact source file, sheet, row, and SHA-256 dual hashes for an ingested record.",
                required_arguments=["source_id", "record_id"],
                argument_schema={
                    "source_id": "string source ID (e.g. SRC-REFUNDS)",
                    "record_id": "string entity or line ID",
                },
                handler=InvestigationTools.retrieve_source_record,
            )
        )

    def register_tool(self, tool_def: ToolDefinition):
        self._tools[tool_def.name] = tool_def

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def get_all_tool_descriptions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "required_arguments": t.required_arguments,
                "schema": t.argument_schema,
            }
            for t in self._tools.values()
        ]

    def execute_tool(
        self,
        request: ToolRequest,
        dataset: IngestedDataset,
        next_ev_idx: int = 1,
    ) -> ToolResult:
        tool_def = self.get_tool(request.tool)
        if not tool_def:
            return ToolResult(
                request_id=request.request_id,
                tool=request.tool,
                success=False,
                output={},
                evidence_items=[],
                error=f"Unregistered tool: '{request.tool}'. Allowed tools: {list(self._tools.keys())}",
            )

        kwargs = dict(request.arguments)
        kwargs["request_id"] = request.request_id
        kwargs["dataset"] = dataset

        # Inject next_ev_idx if accepted
        if "next_ev_idx" in tool_def.handler.__code__.co_varnames:
            kwargs["next_ev_idx"] = next_ev_idx

        try:
            return tool_def.handler(**kwargs)
        except TypeError as e:
            return ToolResult(
                request_id=request.request_id,
                tool=request.tool,
                success=False,
                output={},
                evidence_items=[],
                error=f"Invalid arguments for tool '{request.tool}': {str(e)}",
            )
        except Exception as e:
            return ToolResult(
                request_id=request.request_id,
                tool=request.tool,
                success=False,
                output={},
                evidence_items=[],
                error=f"Execution error in tool '{request.tool}': {str(e)}",
            )
