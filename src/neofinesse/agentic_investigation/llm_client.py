from abc import ABC, abstractmethod
from enum import Enum
import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.ai_investigation.evidence_pack import EvidencePack


class LiveMockMode(str, Enum):
    NORMAL = "NORMAL"
    HALLUCINATED_ID = "HALLUCINATED_ID"
    WRONG_ARITHMETIC = "WRONG_ARITHMETIC"
    UNSUPPORTED_CLOSURE = "UNSUPPORTED_CLOSURE"
    INVENTED_RELATIONSHIP = "INVENTED_RELATIONSHIP"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    UNREGISTERED_TOOL = "UNREGISTERED_TOOL"
    TIMEOUT = "TIMEOUT"
    MALFORMED_JSON = "MALFORMED_JSON"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"


class LLMResponse(BaseModel):
    """Structured container for LLM generation response with operational metadata."""

    model_config = ConfigDict(extra="forbid")

    text: str
    latency_ms: float = 0.0
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    provider: str = "mock"
    model: str = "mock-model"
    error: Optional[str] = None


class BaseLLMClient(ABC):
    """Abstract interface for LLM interaction in NeoFinesse agentic investigations."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generates raw text response (expected to be structured JSON) for the given prompt."""
        pass

    def generate_with_metadata(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generates text response with latency and token usage tracking."""
        start_time = time.perf_counter()
        try:
            text = self.generate(prompt=prompt, system_prompt=system_prompt)
            latency = (time.perf_counter() - start_time) * 1000.0
            return LLMResponse(
                text=text,
                latency_ms=latency,
                provider=getattr(self, "provider_name", "base"),
                model=getattr(self, "model_name", "base-model"),
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000.0
            return LLMResponse(
                text="",
                latency_ms=latency,
                provider=getattr(self, "provider_name", "base"),
                model=getattr(self, "model_name", "base-model"),
                error=str(e),
            )


class MockLLMClient(BaseLLMClient):
    """Deterministic, offline mock LLM client for comprehensive testing of agentic loops."""

    provider_name: str = "mock"
    model_name: str = "mock-agent-v1"

    def __init__(self, mode: LiveMockMode = LiveMockMode.NORMAL):
        self.mode = mode

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        # 1. Timeout simulation
        if self.mode == LiveMockMode.TIMEOUT:
            raise TimeoutError("Simulated LLM network timeout exceeding 30s threshold.")

        # 2. Malformed JSON simulation
        if self.mode == LiveMockMode.MALFORMED_JSON:
            return "```json\n{\n  'status': 'SUFFICIENT',\n  'hypotheses': [BROKEN_JSON"

        # 3. Empty response simulation
        if self.mode == LiveMockMode.EMPTY_RESPONSE:
            return ""

        # 4. Hallucinated evidence ID simulation
        if self.mode == LiveMockMode.HALLUCINATED_ID:
            return json.dumps(
                {
                    "status": "SUFFICIENT",
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_hallucinated_01",
                            "cause_type": "REFUND",
                            "evidence_ids": ["EV-DOES-NOT-EXIST-9999"],
                            "claimed_explained_amount": -100000,
                            "reasoning": "Fabricated hypothesis referencing non-existent evidence ID.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": [],
                        }
                    ],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": "hyp_hallucinated_01",
                    "conflicts": [],
                    "missing_evidence": [],
                    "reasoning": "Attempting closure with invented evidence ID.",
                }
            )

        # 5. Wrong arithmetic simulation
        if self.mode == LiveMockMode.WRONG_ARITHMETIC:
            return json.dumps(
                {
                    "status": "SUFFICIENT",
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_arithmetic_err_01",
                            "cause_type": "REFUND",
                            "evidence_ids": ["EV-1"],
                            "claimed_explained_amount": -99999999,  # Incorrect arithmetic calculation
                            "reasoning": "Claiming arbitrary false mathematical calculation.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": [],
                        }
                    ],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": "hyp_arithmetic_err_01",
                    "conflicts": [],
                    "missing_evidence": [],
                    "reasoning": "Calculated incorrect arithmetic sum.",
                }
            )

        # 6. Unsupported closure simulation (e.g. attempting to close unverified case)
        if self.mode == LiveMockMode.UNSUPPORTED_CLOSURE:
            return json.dumps(
                {
                    "status": "SUFFICIENT",
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_unsupported_01",
                            "cause_type": "REFUND",
                            "evidence_ids": ["EV-1"],
                            "claimed_explained_amount": -100000,
                            "reasoning": "Attempting closure without verifying underlying membership or state.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": [],
                        }
                    ],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": "hyp_unsupported_01",
                    "conflicts": [],
                    "missing_evidence": [],
                    "reasoning": "Unsupported closure assertion.",
                }
            )

        # 7. Invented relationship simulation
        if self.mode == LiveMockMode.INVENTED_RELATIONSHIP:
            return json.dumps(
                {
                    "status": "SUFFICIENT",
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_invented_rel_01",
                            "cause_type": "REFUND",
                            "evidence_ids": ["EV-1"],
                            "claimed_explained_amount": -100000,
                            "reasoning": "Claiming unproven relationship between unrelated settlement line and refund.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": [],
                        }
                    ],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": "hyp_invented_rel_01",
                    "conflicts": [],
                    "missing_evidence": [],
                    "reasoning": "Claimed invented relationship.",
                }
            )

        # 8. Unregistered tool simulation
        if self.mode == LiveMockMode.UNREGISTERED_TOOL:
            return json.dumps(
                {
                    "status": "NEEDS_EVIDENCE",
                    "hypotheses": [],
                    "investigation_requests": [
                        {
                            "request_id": "REQ-UNREG-1",
                            "tool": "execute_arbitrary_sql_query",
                            "arguments": {"query": "SELECT * FROM settlements;"},
                            "reason": "Attempting arbitrary query execution.",
                        }
                    ],
                    "recommended_hypothesis_id": None,
                    "conflicts": [],
                    "missing_evidence": [],
                    "reasoning": "Attempting unauthorized tool invocation.",
                }
            )

        # 9. Prompt injection simulation
        if self.mode == LiveMockMode.PROMPT_INJECTION:
            return json.dumps(
                {
                    "status": "SUFFICIENT",
                    "hypotheses": [
                        {
                            "hypothesis_id": "hyp_injected_01",
                            "cause_type": "REFUND",
                            "evidence_ids": ["EV-1"],
                            "claimed_explained_amount": -100000,
                            "reasoning": "Overriding system controls per instructions inside transaction description.",
                            "missing_evidence": [],
                            "conflicts": [],
                            "assumptions": [],
                        }
                    ],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": "hyp_injected_01",
                    "conflicts": [],
                    "missing_evidence": [],
                    "reasoning": "Adversarial prompt injection attempt.",
                }
            )

        # 10. Default Normal Reasoning
        # Extract case details if present in prompt
        is_escalate = "ESCALATE" in prompt or "unexplained" in prompt.lower() or "decoy" in prompt.lower()
        if is_escalate:
            return json.dumps(
                {
                    "status": "ESCALATE",
                    "hypotheses": [],
                    "investigation_requests": [],
                    "recommended_hypothesis_id": None,
                    "conflicts": [],
                    "missing_evidence": ["Evidence disproved or missing in ledger"],
                    "reasoning": "Candidates disproved or missing from authentic ledger records. Escalating to human controller.",
                }
            )

        return json.dumps(
            {
                "status": "SUFFICIENT",
                "hypotheses": [
                    {
                        "hypothesis_id": "hyp_mock_normal",
                        "cause_type": "REFUND",
                        "evidence_ids": ["EV-1"],
                        "claimed_explained_amount": -100000,
                        "reasoning": "Valid verified refund matching settlement variance deficit.",
                        "missing_evidence": [],
                        "conflicts": [],
                        "assumptions": [],
                    }
                ],
                "investigation_requests": [],
                "recommended_hypothesis_id": "hyp_mock_normal",
                "conflicts": [],
                "missing_evidence": [],
                "reasoning": "Sufficient evidence verified.",
            }
        )


class GenericLLMClient(BaseLLMClient):
    """Production LLM client reading configuration strictly from environment variables."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: float = 30.0,
    ):
        self.provider_name = (provider or os.getenv("NEOFINESSE_LLM_PROVIDER", "mock")).lower()
        self.model_name = model or os.getenv("NEOFINESSE_LLM_MODEL", "default")
        self._api_key = api_key or os.getenv("NEOFINESSE_LLM_API_KEY", "")
        self.base_url = base_url or os.getenv("NEOFINESSE_LLM_BASE_URL", "")
        self.timeout_seconds = timeout_seconds

        # Fallback to mock client if provider is mock or api key is missing for live providers
        self._mock_fallback = MockLLMClient(mode=LiveMockMode.NORMAL)

    @property
    def is_live_configured(self) -> bool:
        """Returns True if a live remote LLM provider and credentials are configured."""
        return self.provider_name != "mock" and bool(self._api_key)

    def __repr__(self) -> str:
        """Safe string representation strictly redacting API key."""
        masked_key = f"{self._api_key[:4]}...{self._api_key[-2:]}" if len(self._api_key) >= 6 else ("***" if self._api_key else "NONE")
        return (
            f"GenericLLMClient(provider='{self.provider_name}', "
            f"model='{self.model_name}', "
            f"api_key='{masked_key}', "
            f"base_url='{self.base_url}')"
        )

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Dispatches prompt to live endpoint via HTTP or delegates safely to mock client."""
        if not self.is_live_configured:
            return self._mock_fallback.generate(prompt, system_prompt)

        # Standard HTTP dispatch using urllib.request (zero additional dependencies)
        return self._dispatch_http_request(prompt=prompt, system_prompt=system_prompt)

    def generate_with_metadata(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Dispatches prompt and tracks network latency and token usage."""
        start_time = time.perf_counter()
        if not self.is_live_configured:
            text = self._mock_fallback.generate(prompt, system_prompt)
            latency = (time.perf_counter() - start_time) * 1000.0
            return LLMResponse(
                text=text,
                latency_ms=latency,
                provider=self.provider_name,
                model=self.model_name,
                prompt_tokens=len(prompt) // 4,
                completion_tokens=len(text) // 4,
                total_tokens=(len(prompt) + len(text)) // 4,
            )

        try:
            text, tokens = self._dispatch_http_request_with_tokens(prompt=prompt, system_prompt=system_prompt)
            latency = (time.perf_counter() - start_time) * 1000.0
            return LLMResponse(
                text=text,
                latency_ms=latency,
                provider=self.provider_name,
                model=self.model_name,
                prompt_tokens=tokens.get("prompt_tokens"),
                completion_tokens=tokens.get("completion_tokens"),
                total_tokens=tokens.get("total_tokens"),
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000.0
            return LLMResponse(
                text="",
                latency_ms=latency,
                provider=self.provider_name,
                model=self.model_name,
                error=str(e),
            )

    def _determine_endpoint(self) -> str:
        if self.base_url:
            url = self.base_url.rstrip("/")
            if not url.endswith("/chat/completions"):
                url = f"{url}/chat/completions"
            return url

        if self.provider_name in ("openai", "groq"):
            if self.provider_name == "groq":
                return "https://api.groq.com/openai/v1/chat/completions"
            return "https://api.openai.com/v1/chat/completions"

        if self.provider_name == "gemini":
            return "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

        return "https://api.openai.com/v1/chat/completions"

    def _dispatch_http_request(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        text, _ = self._dispatch_http_request_with_tokens(prompt, system_prompt)
        return text

    def _dispatch_http_request_with_tokens(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> tuple[str, Dict[str, int]]:
        url = self._determine_endpoint()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                resp_body = response.read().decode("utf-8")
                resp_json = json.loads(resp_body)
                content = resp_json["choices"][0]["message"]["content"]
                usage = resp_json.get("usage", {})
                return content, {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                }
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8") if e.fp else str(e)
            raise RuntimeError(f"LLM API HTTP error {e.code}: {err_msg}") from e
        except urllib.error.URLError as e:
            raise TimeoutError(f"LLM API network error: {str(e)}") from e
