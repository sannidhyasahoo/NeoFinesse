import json
import re
from typing import Optional, Tuple

from pydantic import ValidationError

from neofinesse.agentic_investigation.models import AgentRoundResponse


class AgentResponseParser:
    """Parses and validates structured agent round responses from LLM text."""

    @staticmethod
    def parse_response(raw_text: str) -> Tuple[Optional[AgentRoundResponse], Optional[str]]:
        if not raw_text or not raw_text.strip():
            return None, "Empty response received from agent planner."

        cleaned = raw_text.strip()

        # Extract JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if json_match:
            cleaned = json_match.group(1).strip()

        try:
            parsed_dict = json.loads(cleaned)
        except json.JSONDecodeError as e:
            return None, f"JSON syntax error: {str(e)}"

        try:
            response = AgentRoundResponse.model_validate(parsed_dict)
            return response, None
        except ValidationError as e:
            return None, f"Schema validation error: {str(e)}"
