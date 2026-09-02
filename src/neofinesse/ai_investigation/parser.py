import json
import re
from typing import Optional, Tuple

from pydantic import ValidationError

from neofinesse.ai_investigation.models import AIInvestigationResponse


class AIResponseParser:
    """Robust parser for LLM investigation responses with markdown stripping and schema validation."""

    @staticmethod
    def parse_response(raw_text: str) -> Tuple[Optional[AIInvestigationResponse], Optional[str]]:
        if not raw_text or not raw_text.strip():
            return None, "Empty response received from LLM."

        cleaned = raw_text.strip()

        # 1. Extract JSON from markdown code blocks if present
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if json_match:
            cleaned = json_match.group(1).strip()

        # 2. Parse JSON
        try:
            parsed_dict = json.loads(cleaned)
        except json.JSONDecodeError as e:
            return None, f"JSON syntax error: {str(e)}"

        # 3. Validate against Pydantic schema
        try:
            response = AIInvestigationResponse.model_validate(parsed_dict)
            return response, None
        except ValidationError as e:
            return None, f"Schema validation error: {str(e)}"
