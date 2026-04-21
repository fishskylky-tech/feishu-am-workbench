"""Default LLM adapter using OpenAI or Anthropic API.

Per D-01: Direct OpenAI/Anthropic API call, not 4-platform adapter architecture.
Per D-04: One default adapter using OpenAI/Anthropic API.
Per D-06: Fail-open to keyword mode on LLM failure.

Security:
- API keys via env vars only, never hardcoded
- No API key logging
- Startup validation of required API keys with friendly error messages
"""

from __future__ import annotations

import asyncio
import os
import logging
from enum import Enum
from typing import Literal

logger = logging.getLogger(__name__)


# =============================================================================
# Startup Validation (per OpenCode review: friendly error on missing keys)
# =============================================================================

def validate_api_key_config() -> None:
    """Validate API keys at startup. Call once at module import or early init.

    Raises:
        EnvironmentError: If required API key is missing, with friendly message.

    Per OpenCode review: friendly error message, not silent fallback.
    """
    provider = os.environ.get("LLM_PROVIDER", "openai")
    if provider == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. "
                "Set it in your environment or .env file. "
                "Alternatively, set LLM_PROVIDER=openai to use OpenAI API. "
                "Expert review will fall back to keyword mode if no LLM is available."
            )
    else:
        if not os.environ.get("OPENAI_API_KEY"):
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. "
                "Set it in your environment or .env file. "
                "Alternatively, set LLM_PROVIDER=anthropic to use Anthropic API. "
                "Expert review will fall back to keyword mode if no LLM is available."
            )


class LLMError(Enum):
    """LLM failure types for explicit handling (per OpenCode review)."""
    TIMEOUT = "timeout"
    AUTH_FAILURE = "auth_failure"  # 401
    RATE_LIMIT = "rate_limit"     # 429
    EMPTY_RESPONSE = "empty_response"
    PARSE_FAILURE = "parse_failure"
    API_ERROR = "api_error"        # Non-200, non-429 errors


class DefaultLLMExpertAgent:
    """Default LLM adapter using OpenAI or Anthropic API.

    Per D-01: Uses environment variable LLM_PROVIDER to select OpenAI or Anthropic.
    Per D-04: Single default adapter, not 4-platform architecture.

    Error handling (per OpenCode HIGH concern):
    - Explicit handling for: timeout, auth failure (401), rate limit (429),
      empty response, parse failure
    - All LLM errors inherit from Exception and trigger fallback to keyword mode
    """

    def __init__(
        self,
        expert_name: str,
        prompt_file: str,
        model: str | None = None,
    ):
        self.expert_name = expert_name
        self.prompt_file = prompt_file
        self.model = model or self._default_model()

    def _default_model(self) -> str:
        provider = os.environ.get("LLM_PROVIDER", "openai")
        if provider == "anthropic":
            return "claude-sonnet-4-20250514"
        return "gpt-4o"

    async def invoke(self, prompt: str, context: dict) -> "ExpertReviewResult":
        """Invoke LLM with the given prompt.

        Per D-06: Fail-open to keyword mode on any LLMError.
        Per OpenCode review: explicit error types for timeout, auth, rate limit,
        empty response, parse failure.
        """
        from runtime.expert_agent_invoker import ExpertReviewResult

        provider = os.environ.get("LLM_PROVIDER", "openai")

        # Validate API key presence (fail-open to keyword if missing)
        if provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise EnvironmentError("ANTHROPIC_API_KEY not set")
        else:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise EnvironmentError("OPENAI_API_KEY not set")

        try:
            if provider == "anthropic":
                result_text = await self._invoke_anthropic(prompt, api_key)
            else:
                result_text = await self._invoke_openai(prompt, api_key)

            return self._parse_result(result_text, context, in_eval_context=False)

        except asyncio.TimeoutError:
            logger.warning(f"LLM timeout for {self.expert_name}")
            raise  # Re-raise for fallback handling in caller

        except KeyboardInterrupt:
            raise  # Re-raise, do not fallback

        except Exception as e:
            error_type = self._classify_error(e)
            logger.warning(f"LLM invocation failed for {self.expert_name}: {error_type} — {e}")
            raise  # Re-raise for fallback handling in caller

    def _classify_error(self, error: Exception) -> LLMError:
        """Classify LLM error into explicit type (per OpenCode review)."""
        error_str = str(error).lower()
        error_type_str = type(error).__name__.lower()

        # Timeout detection
        if "timeout" in error_str or "timed out" in error_str:
            return LLMError.TIMEOUT

        # Auth failure (401)
        if "401" in error_str or "unauthorized" in error_str or "invalid api key" in error_str:
            return LLMError.AUTH_FAILURE

        # Rate limit (429)
        if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
            return LLMError.RATE_LIMIT

        # Empty response
        if "empty" in error_str or "none" in error_str:
            return LLMError.EMPTY_RESPONSE

        # Parse failure
        if "parse" in error_str or "json" in error_str or "decode" in error_str:
            return LLMError.PARSE_FAILURE

        # Default to API error
        return LLMError.API_ERROR

    async def _invoke_openai(self, prompt: str, api_key: str) -> str:
        """Call OpenAI API with timeout handling."""
        import openai
        from openai import APIError, RateLimitError, AuthenticationError

        client = openai.OpenAI(api_key=api_key, timeout=30.0)  # 30s timeout

        def _call() -> str:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
            return content

        try:
            return await asyncio.to_thread(_call)

        except RateLimitError as e:
            logger.warning(f"OpenAI rate limit hit: {e}")
            raise

        except AuthenticationError as e:
            logger.warning(f"OpenAI auth failed: {e}")
            raise

        except Exception as e:
            logger.warning(f"OpenAI API error: {e}")
            raise

    async def _invoke_anthropic(self, prompt: str, api_key: str) -> str:
        """Call Anthropic API with timeout handling."""
        import anthropic
        from anthropic import APIError, RateLimitError, AuthenticationError

        client = anthropic.Anthropic(api_key=api_key, timeout=30.0)  # 30s timeout

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text if response.content else ""
            if not content:
                raise ValueError("Empty response from Anthropic")
            return content

        except RateLimitError as e:
            logger.warning(f"Anthropic rate limit hit: {e}")
            raise

        except AuthenticationError as e:
            logger.warning(f"Anthropic auth failed: {e}")
            raise

        except Exception as e:
            logger.warning(f"Anthropic API error: {e}")
            raise

    def _check_hallucination(self, findings: list[str], check_signals: list[str]) -> tuple[bool, str | None]:
        """Check if any finding references a signal not in check_signals.

        Returns (has_hallucination, block_reason).
        Signal comparison is case-insensitive and whitespace-tolerant.
        """
        import re
        fabricated = []
        signal_pattern = re.compile(r'^(PASS|FLAG|BLOCK):\s*([^\n]+)')

        for finding in findings:
            match = signal_pattern.match(finding)
            if match:
                # Normalize: strip trailing punctuation, whitespace, lowercase for comparison
                signal = re.sub(r'[^\w\s-]', '', match.group(2)).strip().lower()
                if check_signals and signal not in [s.strip().lower() for s in check_signals]:
                    fabricated.append(signal)

        if fabricated:
            # Per review MEDIUM fix: block entire result if ANY fabricated signal detected
            return True, f"fabricated_signal: {fabricated[0]} not in check_signals"
        return False, None

    def _parse_result(self, text: str, context: dict | None = None, in_eval_context: bool = False) -> "ExpertReviewResult":
        """Parse LLM response into ExpertReviewResult.

        Expected format from agency-agents prompts:
        - PASS: signal found
        - FLAG: signal missing/blocked

        Per OpenCode review: explicit handling for empty or malformed response.

        in_eval_context: If True, allows "accept all" fallback when check_signals is empty.
                         If False (production), check_signals is required and missing = parse error.

        Returns ExpertReviewResult with findings list.
        Raises ValueError on parse failure (caller handles fallback).
        """
        from runtime.expert_agent_invoker import ExpertReviewResult

        if not text or not text.strip():
            raise ValueError("Empty response from LLM")

        findings: list[str] = []
        passed = True
        blocked = False
        block_reason = None

        check_signals = (context or {}).get("check_signals", [])

        try:
            for line in text.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line.startswith("PASS:"):
                    findings.append(line)
                elif line.startswith("FLAG:"):
                    findings.append(line)
                    passed = False
                elif line.startswith("BLOCK:"):
                    findings.append(line)
                    passed = False
                    blocked = True
                    block_reason = line[7:].strip() if len(line) > 7 else "LLM blocked"

            if not findings:
                # No parseable findings — treat as parse failure
                raise ValueError(f"No parseable findings in LLM response: {text[:100]}")

            # Hallucination check (per review HIGH fix: scoped to eval context only)
            if check_signals:
                # Normal mode: validate against check_signals
                has_hallucination, hallucination_reason = self._check_hallucination(findings, check_signals)
                if has_hallucination:
                    blocked = True
                    passed = False
                    block_reason = hallucination_reason
            elif in_eval_context:
                # Eval context fallback: no check_signals means accept all (backward compat for old evals)
                # Documented in eval runner — NOT for production use
                pass
            else:
                # Production: no check_signals is a parse error, not silent accept-all
                raise ValueError("check_signals missing in production context — hallucination guardrail requires validation list")

        except ValueError:
            raise  # Re-raise parse errors for fallback handling

        return ExpertReviewResult(
            expert_name=self.expert_name,
            findings=findings,
            passed=passed,
            blocked=blocked,
            block_reason=block_reason,
            invocation_metadata={
                "provider": os.environ.get("LLM_PROVIDER", "openai"),
                "model": self.model,
            },
        )

    def supports_parallel(self) -> bool:
        return True

    def get_platform(self) -> Literal["openai", "anthropic"]:
        provider = os.environ.get("LLM_PROVIDER", "openai")
        return provider
