from typing import Optional, Set, Tuple

from neofinesse.agentic_investigation.models import InvestigationBudget, ToolRequest
from neofinesse.agentic_investigation.state import InvestigationState
from neofinesse.agentic_investigation.tool_registry import ToolRegistry


class ToolRequestValidator:
    """Strict validation layer preventing unauthorized, unbounded, duplicate, or malformed tool calls."""

    @staticmethod
    def validate_request(
        request: ToolRequest,
        registry: ToolRegistry,
        state: InvestigationState,
        budget: InvestigationBudget,
    ) -> Tuple[bool, Optional[str]]:
        # 1. Check tool registration
        if not registry.has_tool(request.tool):
            return False, f"Unknown tool '{request.tool}'. Allowed tools: {list(registry._tools.keys())}"

        tool_def = registry.get_tool(request.tool)
        if not tool_def:
            return False, f"Tool definition not found for '{request.tool}'"

        # 2. Check required arguments
        for req_arg in tool_def.required_arguments:
            if req_arg not in request.arguments or request.arguments[req_arg] is None or request.arguments[req_arg] == "":
                return False, f"Missing required argument '{req_arg}' for tool '{request.tool}'"

        # 3. Check for unbounded/wildcard/dangerous inputs
        for k, v in request.arguments.items():
            if isinstance(v, str):
                v_lower = v.strip().lower()
                if v_lower in ("*", "all", "everything", "any", "%"):
                    return False, f"Wildcard/unbounded queries not permitted in argument '{k}'"
                if any(sql in v_lower for sql in ("select ", "drop ", "delete ", "update ", "insert ", "exec ")):
                    return False, f"SQL or command injection patterns rejected in argument '{k}'"

        # 4. Check temporal window limits
        if request.tool == "retrieve_temporal_neighbors":
            wb = request.arguments.get("window_before_minutes", 0)
            wa = request.arguments.get("window_after_minutes", 0)
            if not isinstance(wb, (int, float)) or not isinstance(wa, (int, float)) or wb < 0 or wa < 0:
                return False, "Temporal window minutes must be non-negative numbers"
            if wb > 180 or wa > 180:
                return False, "Temporal window exceeds maximum allowable limit of 180 minutes"

        # 5. Check duplicate execution
        current_sig = f"{request.tool}:{sorted(request.arguments.items())}"
        for prev_req in state.completed_requests:
            prev_sig = f"{prev_req.tool}:{sorted(prev_req.arguments.items())}"
            if current_sig == prev_sig:
                return False, f"Duplicate tool call: '{request.tool}' with identical arguments already executed in this investigation"

        # 6. Check budget limits
        if len(state.completed_requests) >= budget.max_tool_calls:
            return False, f"Tool call budget exhausted ({len(state.completed_requests)}/{budget.max_tool_calls} tool calls used)"

        return True, None
