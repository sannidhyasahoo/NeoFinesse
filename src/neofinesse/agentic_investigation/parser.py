import json
import re
from typing import Any, Dict, Optional, Tuple

from pydantic import ValidationError

from neofinesse.agentic_investigation.models import AgentInvestigationStatus, AgentRoundResponse


class AgentResponseParser:
    """Parses, normalizes, and validates structured agent round responses from LLM output."""

    @staticmethod
    def parse_response(raw_text: str) -> Tuple[Optional[AgentRoundResponse], Optional[str]]:
        if not raw_text or not raw_text.strip():
            return None, "EMPTY_LLM_RESPONSE: Received empty or whitespace-only response from LLM."

        cleaned = raw_text.strip()

        # Extract JSON from markdown code blocks if present
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if json_match:
            cleaned = json_match.group(1).strip()

        try:
            parsed_dict = json.loads(cleaned)
        except json.JSONDecodeError as e:
            return None, f"MALFORMED_JSON: JSON syntax decoding failed: {str(e)}"

        if not isinstance(parsed_dict, dict):
            return None, f"INVALID_LLM_RESPONSE: Expected JSON object at root, got {type(parsed_dict).__name__}."

        # Normalize common LLM field variations
        normalized = AgentResponseParser._normalize_aliases(parsed_dict)

        try:
            response = AgentRoundResponse.model_validate(normalized)
            return response, None
        except ValidationError as e:
            return None, f"SCHEMA_VALIDATION_ERROR: Output failed Pydantic schema validation: {str(e)}"

    @staticmethod
    def _normalize_aliases(data: Dict[str, Any]) -> Dict[str, Any]:
        norm = dict(data)

        # 1. Alias: evidence_gaps -> missing_evidence
        if "evidence_gaps" in norm and "missing_evidence" not in norm:
            norm["missing_evidence"] = norm.pop("evidence_gaps")

        # 2. Alias: tool_requests -> investigation_requests
        if "tool_requests" in norm and "investigation_requests" not in norm:
            norm["investigation_requests"] = norm.pop("tool_requests")

        # 3. Alias: reasoning_summary -> reasoning
        if "reasoning_summary" in norm and "reasoning" not in norm:
            norm["reasoning"] = norm.pop("reasoning_summary")

        # 4. Status inference if omitted
        if "status" not in norm or not norm["status"]:
            inv_reqs = norm.get("investigation_requests", [])
            hyps = norm.get("hypotheses", [])
            if inv_reqs:
                norm["status"] = AgentInvestigationStatus.NEEDS_EVIDENCE.value
            elif hyps:
                norm["status"] = AgentInvestigationStatus.SUFFICIENT.value
            else:
                norm["status"] = AgentInvestigationStatus.ESCALATE.value
        elif isinstance(norm["status"], str):
            norm["status"] = norm["status"].upper()

        # 5. Default empty collections
        if "hypotheses" not in norm or not isinstance(norm["hypotheses"], list):
            norm["hypotheses"] = []
        if "investigation_requests" not in norm or not isinstance(norm["investigation_requests"], list):
            norm["investigation_requests"] = []
        if "conflicts" not in norm or not isinstance(norm["conflicts"], list):
            norm["conflicts"] = []
        if "missing_evidence" not in norm or not isinstance(norm["missing_evidence"], list):
            norm["missing_evidence"] = []
        if "reasoning" not in norm:
            norm["reasoning"] = "No reasoning summary provided."

        # 6. Normalize hypotheses items
        normalized_hyps = []
        for idx, h in enumerate(norm["hypotheses"]):
            if isinstance(h, dict):
                h_norm = dict(h)
                if "hypothesis_id" not in h_norm:
                    h_norm["hypothesis_id"] = f"hyp_{idx + 1}"
                if "claimed_explained_amount" not in h_norm:
                    if "claimed_amount" in h_norm:
                        h_norm["claimed_explained_amount"] = h_norm.pop("claimed_amount")
                    elif "amount" in h_norm:
                        h_norm["claimed_explained_amount"] = h_norm.pop("amount")
                    else:
                        h_norm["claimed_explained_amount"] = 0
                if "evidence_ids" not in h_norm or not isinstance(h_norm["evidence_ids"], list):
                    h_norm["evidence_ids"] = []
                if "reasoning" not in h_norm:
                    h_norm["reasoning"] = "Hypothesis explanation."
                normalized_hyps.append(h_norm)
        norm["hypotheses"] = normalized_hyps

        return norm
