from abc import ABC, abstractmethod
from enum import Enum
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
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


def _load_dotenv_if_present(dotenv_path: str = ".env") -> None:
    """Loads key-value pairs from .env into os.environ if present without external dependencies."""
    p = Path(dotenv_path)
    if not p.exists() or not p.is_file():
        return
    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, v = s.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and v and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


class GenericLLMClient(BaseLLMClient):
    """Production LLM client reading configuration strictly from environment variables."""

    @staticmethod
    def _normalize_model_name(provider: str, model: Optional[str]) -> str:
        """Normalizes model names, supporting shorthand aliases and common variations."""
        if not model or model.strip().lower() in ("default", "none", ""):
            if provider == "gemini":
                return "gemini-2.5-flash"
            if provider == "groq":
                return "llama-3.3-70b-versatile"
            if provider == "openai":
                return "gpt-4o-mini"
            return "default"

        raw = model.strip()
        cleaned = raw.lower().replace(" ", "-")

        # Fix common typos (e.g. "flah" -> "flash")
        cleaned = cleaned.replace("flah", "flash")

        # Gemini normalization (supports 3.7 flash, 3.8 flash, 2.5 flash, 2.0 flash, etc.)
        if provider == "gemini" or "gemini" in cleaned:
            if cleaned in ("3.7-flash", "3.7", "flash-3.7", "gemini-3.7-flah", "gemini-3.7-flash"):
                return "gemini-3.7-flash"
            if cleaned in ("3.8-flash", "3.8", "flash-3.8", "gemini-3.8-flah", "gemini-3.8-flash"):
                return "gemini-3.8-flash"
            if cleaned in ("2.5-flash", "2.5", "flash-2.5", "gemini-2.5-flash"):
                return "gemini-2.5-flash"
            if cleaned in ("2.0-flash", "2.0", "flash-2.0", "gemini-2.0-flash"):
                return "gemini-2.0-flash"
            if cleaned in ("1.5-flash", "1.5", "flash-1.5", "gemini-1.5-flash"):
                return "gemini-1.5-flash"
            if cleaned in ("1.5-pro", "gemini-1.5-pro"):
                return "gemini-1.5-pro"
            if not cleaned.startswith("gemini-") and any(v in cleaned for v in ("flash", "pro")):
                return f"gemini-{cleaned}"
            return cleaned

        # Groq normalization (supports opennaioss-20b, 120b, openai/gpt-oss-20b, etc.)
        if provider == "groq" or any(k in cleaned for k in ("oss", "groq", "llama", "mixtral")):
            if any(cleaned == x for x in ("20b", "oss-20b", "gpt-oss-20b", "openaioss-20b", "opennaioss-20b", "openai/gpt-oss-20b")):
                return "openai/gpt-oss-20b"
            if any(cleaned == x for x in ("120b", "oss-120b", "gpt-oss-120b", "openaioss-120b", "opennaioss-120b", "openai/gpt-oss-120b")):
                return "openai/gpt-oss-120b"
            if "opennaioss" in cleaned:
                return cleaned.replace("opennaioss", "openai/gpt-oss")
            if "openaioss" in cleaned:
                return cleaned.replace("openaioss", "openai/gpt-oss")
            if cleaned.startswith("gpt-oss-"):
                return f"openai/{cleaned}"
            return raw

        return raw

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: float = 30.0,
        force_live: bool = False,
        allow_model_fallback: bool = True,
        request_delay_seconds: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        _load_dotenv_if_present()
        raw_model = model or os.getenv("NEOFINESSE_LLM_MODEL", "")

        if provider:
            raw_provider = provider
        else:
            # Auto-detect from model name first if unambiguous
            mod_low = raw_model.lower()
            if "gemini" in mod_low:
                raw_provider = "gemini"
            elif any(k in mod_low for k in ("groq", "oss", "opennaioss", "llama", "mixtral")):
                raw_provider = "groq"
            elif any(k in mod_low for k in ("gpt-4", "gpt-3.5", "o1", "o3")):
                raw_provider = "openai"
            else:
                raw_provider = os.getenv("NEOFINESSE_LLM_PROVIDER", "")
                if not raw_provider:
                    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
                        raw_provider = "gemini"
                    elif os.getenv("GROQ_API_KEY"):
                        raw_provider = "groq"
                    elif os.getenv("OPENAI_API_KEY"):
                        raw_provider = "openai"
                    else:
                        raw_provider = "mock"

        self.provider_name = raw_provider.lower()
        self.model_name = self._normalize_model_name(self.provider_name, raw_model)
        self.requested_model = self.model_name
        self.effective_model = self.model_name
        self.fallback_triggered: bool = False
        self.fallback_reason: Optional[str] = None

        # Retrieve API key with provider-specific fallback
        key = api_key or os.getenv("NEOFINESSE_LLM_API_KEY", "")
        if not key:
            if self.provider_name == "gemini":
                key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
            elif self.provider_name == "groq":
                key = os.getenv("GROQ_API_KEY") or ""
            elif self.provider_name == "openai":
                key = os.getenv("OPENAI_API_KEY") or ""
        self._api_key = key

        self.base_url = base_url or os.getenv("NEOFINESSE_LLM_BASE_URL", "")
        self.timeout_seconds = timeout_seconds
        self._force_live = force_live

        # Controlled benchmark configuration
        # allow_model_fallback=False → only the exact requested model is tried; no silent substitution
        self.allow_model_fallback: bool = allow_model_fallback

        # Inter-request rate pacing (free tier: 4s recommended; 0 = disabled)
        _delay_env = os.getenv("NEOFINESSE_LLM_REQUEST_DELAY_SECONDS", "0")
        self.request_delay_seconds: float = request_delay_seconds if request_delay_seconds is not None else float(_delay_env)

        # Per-model retry budget for transient errors (429, 503)
        _retries_env = os.getenv("NEOFINESSE_LLM_MAX_RETRIES", "3")
        self.max_retries: int = max_retries if max_retries is not None else int(_retries_env)

        # Per-run telemetry (reset on each benchmark run)
        self.retry_log: List[Dict[str, Any]] = []
        self.total_429_count: int = 0
        self.total_timeout_count: int = 0
        self._last_request_time: float = 0.0

        # Fallback to mock client if provider is mock or api key is missing for live providers
        self._mock_fallback = MockLLMClient(mode=LiveMockMode.NORMAL)

    @property
    def is_live_configured(self) -> bool:
        """Returns True if a live remote LLM provider and credentials are configured."""
        return self.provider_name != "mock" and bool(self._api_key)

    @property
    def is_live_enabled(self) -> bool:
        """Returns True only when credentials are valid AND remote execution is explicitly enabled."""
        if not self.is_live_configured:
            return False
        if getattr(self, "_force_live", False):
            return True
        return os.getenv("NEOFINESSE_RUN_LIVE_TESTS", "").strip().lower() in ("1", "true", "yes")

    def get_diagnostic(self) -> Dict[str, Any]:
        """Returns safe configuration diagnostic without revealing secrets."""
        has_key = bool(self._api_key)
        masked_key = f"{self._api_key[:4]}...{self._api_key[-2:]}" if len(self._api_key) >= 6 else ("***" if has_key else "absent")
        return {
            "provider": f"configured ({self.provider_name})" if self.provider_name != "mock" else "unconfigured (mock)",
            "model": f"configured ({self.model_name})" if self.model_name != "default" else "unconfigured (default)",
            "requested_model": self.requested_model,
            "effective_model": self.effective_model,
            "fallback_triggered": self.fallback_triggered,
            "fallback_reason": self.fallback_reason,
            "api_key": f"present ({masked_key})" if has_key else "absent",
            "base_url": f"configured ({self.base_url})" if self.base_url else "default",
            "remote_mode": self.is_live_enabled,
            "allow_model_fallback": self.allow_model_fallback,
            "request_delay_seconds": self.request_delay_seconds,
            "max_retries": self.max_retries,
        }

    def format_diagnostic(self) -> str:
        """Formats the configuration diagnostic into human-readable text."""
        diag = self.get_diagnostic()
        fb_str = f"{diag['fallback_triggered']} (reason: {diag['fallback_reason']})" if diag['fallback_triggered'] else "false"
        lines = [
            f"Provider:              {diag['provider']}",
            f"Requested Model:       {diag['requested_model']}",
            f"Effective Model:       {diag['effective_model']}",
            f"Fallback Triggered:    {fb_str}",
            f"Allow Model Fallback:  {diag['allow_model_fallback']}",
            f"Request Delay:         {diag['request_delay_seconds']}s",
            f"Max Retries:           {diag['max_retries']}",
            f"API key:               {diag['api_key']}",
            f"Base URL:              {diag['base_url']}",
            f"Remote mode:           {'true' if diag['remote_mode'] else 'false'}",
        ]
        return "\n".join(lines)

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
        if not self.is_live_enabled:
            return self._mock_fallback.generate(prompt, system_prompt)

        # Standard HTTP dispatch using urllib.request (zero additional dependencies)
        return self._dispatch_http_request(prompt=prompt, system_prompt=system_prompt)

    def generate_with_metadata(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Dispatches prompt and tracks network latency and token usage."""
        start_time = time.perf_counter()
        if not self.is_live_enabled:
            text = self._mock_fallback.generate(prompt, system_prompt)
            latency = (time.perf_counter() - start_time) * 1000.0
            return LLMResponse(
                text=text,
                latency_ms=latency,
                provider="mock (offline fallback)",
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

    def _apply_request_pacing(self) -> None:
        """Enforces configurable inter-request delay to respect API rate limits.

        Only fires when:
        - ``request_delay_seconds > 0``
        - This is the second or subsequent call (``_last_request_time > 0``)
        """
        if self.request_delay_seconds <= 0:
            return
        if self._last_request_time > 0:
            elapsed = time.monotonic() - self._last_request_time
            wait = max(0.0, self.request_delay_seconds - elapsed)
            if wait > 0:
                time.sleep(wait)
        self._last_request_time = time.monotonic()

    def _dispatch_http_request_with_tokens(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> tuple[str, Dict[str, int]]:
        # Apply inter-request pacing before each remote call
        self._apply_request_pacing()

        url = self._determine_endpoint()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }
        if self.provider_name == "gemini":
            headers["x-goog-api-key"] = self._api_key

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        base_payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }

        def _execute_post(post_payload: dict) -> tuple[str, Dict[str, int]]:
            req_data = json.dumps(post_payload).encode("utf-8")
            req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
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

        # Build model candidate list:
        # - allow_model_fallback=True  → original resilience behaviour (tries 2.5/2.0/1.5 on 503/404)
        # - allow_model_fallback=False → strict single-model; 503/404 raises, no substitution
        models_to_try = [self.model_name]
        if self.allow_model_fallback and self.provider_name == "gemini":
            for fb in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
                if fb not in models_to_try:
                    models_to_try.append(fb)

        last_err: Optional[Exception] = None
        for idx, m in enumerate(models_to_try):
            cur_payload = dict(base_payload)
            cur_payload["model"] = m

            # --- Per-model retry loop (handles 429) ---
            for attempt in range(1, self.max_retries + 2):  # up to max_retries retries
                try:
                    content, tokens = _execute_post(cur_payload)
                    self.effective_model = m
                    if idx > 0:
                        self.fallback_triggered = True
                    self.model_name = m
                    return content, tokens

                except urllib.error.HTTPError as e:
                    err_msg = e.read().decode("utf-8") if e.fp else str(e)

                    # ── json_object / schema 400 → retry without response_format ──
                    if e.code == 400 and any(k in err_msg.lower() for k in ("response_format", "json_object", "schema")):
                        try:
                            nofmt_payload = dict(cur_payload)
                            nofmt_payload.pop("response_format", None)
                            content, tokens = _execute_post(nofmt_payload)
                            self.effective_model = m
                            if idx > 0:
                                self.fallback_triggered = True
                            self.model_name = m
                            return content, tokens
                        except Exception:
                            pass  # fall through to raise

                    # ── 429 quota exhaustion → bounded backoff with retryDelay extraction ──
                    if e.code == 429:
                        self.total_429_count += 1
                        if attempt <= self.max_retries:
                            retry_delay_val = None
                            # 1. Inspect Retry-After header first
                            retry_after_raw = e.headers.get("Retry-After") if hasattr(e, "headers") and e.headers else None
                            if retry_after_raw:
                                try:
                                    retry_delay_val = float(retry_after_raw)
                                except (ValueError, TypeError):
                                    pass
                            # 2. Inspect error payload for Gemini-style retryDelay (e.g. "retryDelay": "28s" or "retry in 28.8s")
                            if retry_delay_val is None and err_msg:
                                m_delay = re.search(r'retry in\s+([\d\.]+)\s*s', err_msg, re.IGNORECASE)
                                if not m_delay:
                                    m_delay = re.search(r'"retryDelay":\s*"(\d+)\s*s?"', err_msg)
                                if m_delay:
                                    try:
                                        retry_delay_val = float(m_delay.group(1)) + 1.0
                                    except (ValueError, TypeError):
                                        pass
                            if retry_delay_val is not None:
                                backoff = min(retry_delay_val, 60.0)
                            else:
                                backoff = min(2.0 ** attempt, 60.0)
                            self.retry_log.append({
                                "model": m,
                                "attempt": attempt,
                                "status": 429,
                                "backoff_seconds": backoff,
                                "reason": "RESOURCE_EXHAUSTED",
                            })
                            time.sleep(backoff)
                            continue  # retry same model
                        # All retries exhausted for 429
                        raise RuntimeError(f"LLM API HTTP error {e.code}: {err_msg}") from e

                    # ── 503 temporary demand spike → retry same model with exponential backoff ──
                    if e.code == 503:
                        if attempt <= self.max_retries:
                            backoff = min(2.0 ** attempt, 30.0)
                            self.retry_log.append({
                                "model": m,
                                "attempt": attempt,
                                "status": 503,
                                "backoff_seconds": backoff,
                                "reason": "HIGH_DEMAND_SPIKE",
                            })
                            time.sleep(backoff)
                            continue  # retry same model
                        # Retries on this model exhausted; if multi-model fallback allowed, try next model
                        if len(models_to_try) > 1:
                            self.fallback_triggered = True
                            self.fallback_reason = f"HTTP 503 (retries exhausted)"
                            last_err = RuntimeError(f"LLM API HTTP error {e.code}: {err_msg}")
                            break
                        raise RuntimeError(f"LLM API HTTP error {e.code}: {err_msg}") from e

                    # ── 404 model not found ──
                    if e.code == 404 and len(models_to_try) > 1:
                        self.fallback_triggered = True
                        self.fallback_reason = f"HTTP 404"
                        last_err = RuntimeError(f"LLM API HTTP error {e.code}: {err_msg}")
                        break

                    # ── All other HTTP errors → raise immediately ──
                    raise RuntimeError(f"LLM API HTTP error {e.code}: {err_msg}") from e

                except urllib.error.URLError as e:
                    self.total_timeout_count += 1
                    raise TimeoutError(f"LLM API network error: {str(e)}") from e
            else:
                # Inner loop exhausted without break (429 retries depleted)
                continue  # move to next model if available

        if last_err:
            raise last_err
