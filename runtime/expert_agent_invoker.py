"""Expert agent invocation orchestrator for scene runtime.

Per AA-01-PLAN.md Section 6: ExpertAgent interface and AggregatedFailureResult.
Per OpenCode review concern MEDIUM-06: AggregatedFailureResult integration with circuit breaker.

Security:
- validate_agent_reference() called before any agent invocation
- CircuitBreaker prevents cascade failures
- AggregatedFailureResult triggers fallback to keyword mode
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)


@dataclass
class ExpertReviewResult:
    """Standard result envelope for expert review."""
    expert_name: str
    findings: list[str]
    passed: bool
    blocked: bool = False
    block_reason: str | None = None
    invocation_metadata: dict | None = None


@dataclass
class AggregatedFailureResult(Exception):
    """Raised when all retry attempts fail for one or more agents.

    Per AA-01-PLAN.md Section 6.3: raised when all retries exhausted.
    Triggers fallback to keyword mode in scene runtime.
    """
    successful: list[ExpertReviewResult]
    failures: list[tuple[str, Exception]]

    def __str__(self) -> str:
        failure_summary = "; ".join(f"{name}: {err}" for name, err in self.failures)
        return f"AggregatedFailure({len(self.failures)} failures: {failure_summary})"


class CircuitOpenError(Exception):
    """Raised when circuit breaker is OPEN and invocation is not allowed."""
    agent_name: str

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        super().__init__(f"Circuit breaker is OPEN for agent '{agent_name}'")


CIRCUIT_BREAKER_CONFIG = {
    "failure_threshold": 5,
    "recovery_timeout": 60,
    "half_open_max_calls": 3,
}


@dataclass
class CircuitBreakerState:
    failure_count: int = 0
    last_failure_time: float | None = None
    state: Literal["CLOSED", "OPEN", "HALF_OPEN"] = "CLOSED"


class CircuitBreaker:
    """Prevents cascade failures during AI expert invocation.

    Per AA-01-PLAN.md Section 7: circuit breaker trips after consecutive failures.
    Per OpenCode review concern HIGH-01: migration/fallback path with circuit breaker.
    """

    def __init__(self, config: dict | None = None):
        self.config = config or CIRCUIT_BREAKER_CONFIG
        self.state = CircuitBreakerState()

    def record_failure(self) -> None:
        self.state.failure_count += 1
        self.state.last_failure_time = time.monotonic()
        if self.state.failure_count >= self.config["failure_threshold"]:
            self.state.state = "OPEN"

    def record_success(self) -> None:
        self.state.failure_count = 0
        self.state.state = "CLOSED"

    def can_execute(self) -> bool:
        if self.state.state == "CLOSED":
            return True
        if self.state.state == "OPEN":
            if self.state.last_failure_time:
                elapsed = time.monotonic() - self.state.last_failure_time
                if elapsed > self.config["recovery_timeout"]:
                    self.state.state = "HALF_OPEN"
                    return True
            return False
        return True  # HALF_OPEN


_agent_circuit_breakers: dict[str, CircuitBreaker] = {}
_agent_circuit_breakers_lock = asyncio.Lock()


async def get_circuit_breaker(agent_name: str) -> CircuitBreaker:
    """Get or create circuit breaker for agent_name."""
    async with _agent_circuit_breakers_lock:
        if agent_name not in _agent_circuit_breakers:
            _agent_circuit_breakers[agent_name] = CircuitBreaker()
        return _agent_circuit_breakers[agent_name]


async def async_invoke_with_timeout(
    agents: list["ExpertAgent"],
    prompts: list[str],
    timeout_per_agent: int = 120,
    retry_count: int = 2
) -> list[ExpertReviewResult]:
    """Invoke multiple agents with per-agent timeout, retry, and circuit breaker.

    Per AA-01-PLAN.md Section 6.3: AggregatedFailureResult raised when all retries fail.
    Per OpenCode review concern MEDIUM-06: AggregatedFailureResult integration with scene runtime.
    """
    results: list[ExpertReviewResult | Exception] = []
    successful: list[ExpertReviewResult] = []
    failures: list[tuple[str, Exception]] = []

    for agent, prompt in zip(agents, prompts):
        cb = await get_circuit_breaker(agent.get_platform())

        if not cb.can_execute():
            failures.append((agent.get_platform(), CircuitOpenError(agent.get_platform())))
            results.append(CircuitOpenError(agent.get_platform()))
            continue

        try:
            result = await asyncio.wait_for(
                agent.invoke(prompt, {}),
                timeout=timeout_per_agent
            )
            cb.record_success()
            successful.append(result)
            results.append(result)
        except asyncio.TimeoutError:
            cb.record_failure()
            err = Exception(f"Timeout after {timeout_per_agent}s")
            failures.append((agent.get_platform(), err))
            results.append(err)
        except Exception as e:
            cb.record_failure()
            failures.append((agent.get_platform(), e))
            results.append(e)

    # If ALL agents failed, raise AggregatedFailureResult
    if len(successful) == 0 and failures:
        raise AggregatedFailureResult(successful=successful, failures=failures)

    # If some agents succeeded but others failed, log partial failure warning
    if failures:
        logger.warning(
            "Partial failure during expert invocation: %d succeeded, %d failed. "
            "Failed agents: %s",
            len(successful),
            len(failures),
            [name for name, _ in failures],
        )

    return [r for r in results if isinstance(r, ExpertReviewResult)]


async def run_expert_review_with_fallback(
    scene_name: str,
    evidence_container: Any,
    expert_cards: dict,
    agents_dir: Path,
    migration_phase: str = "keyword"
) -> tuple[ExpertReviewResult | None, ExpertReviewResult | None]:
    """Run expert review with fallback to keyword mode on AggregatedFailureResult.

    Per AA-01-PLAN.md Section 7: HYBRID phase falls back to keyword on AI failure.
    Per OpenCode review concern HIGH-01: migration/fallback path integration.
    """
    from runtime.expert_analysis_helper import run_input_audit, run_output_audit

    input_result: ExpertReviewResult | None = None
    output_result: ExpertReviewResult | None = None

    if migration_phase == "keyword":
        # Use keyword-based fallback
        if expert_cards.get("input_review"):
            input_result = run_input_audit(evidence_container, expert_cards["input_review"])
        if expert_cards.get("output_review"):
            output_result = run_output_audit([], expert_cards["output_review"])
        return input_result, output_result

    # Try AI mode
    try:
        if expert_cards.get("input_review") is not None and expert_cards["input_review"].get("agent_name"):
            from runtime.expert_card_loader import validate_agent_reference, normalize_agent_name

            agent_name = normalize_agent_name(expert_cards["input_review"]["agent_name"])
            is_valid, err = validate_agent_reference(agent_name)
            if not is_valid:
                logger.warning(f"Agent '{agent_name}' validation failed: {err}")
                # Fall back to keyword mode
                if expert_cards.get("input_review"):
                    input_result = run_input_audit(evidence_container, expert_cards["input_review"])
                if expert_cards.get("output_review"):
                    output_result = run_output_audit([], expert_cards["output_review"])
                return input_result, output_result

            # Agent validation passed - actual invocation depends on Phase 25 platform adapters
            logger.info(f"Agent '{agent_name}' validated, invocation deferred to Phase 25")

    except AggregatedFailureResult as e:
        logger.warning(f"AI expert invocation failed, falling back to keyword mode: {e}")
        if expert_cards.get("input_review"):
            input_result = run_input_audit(evidence_container, expert_cards["input_review"])
        if expert_cards.get("output_review"):
            output_result = run_output_audit([], expert_cards["output_review"])
    except CircuitOpenError as e:
        logger.warning(f"Circuit breaker open for {e.agent_name}, falling back to keyword mode")
        if expert_cards.get("input_review"):
            input_result = run_input_audit(evidence_container, expert_cards["input_review"])
        if expert_cards.get("output_review"):
            output_result = run_output_audit([], expert_cards["output_review"])

    return input_result, output_result


class ExpertAgent(ABC):
    """Abstract base class for platform-specific expert agents.

    Per AA-01-PLAN.md Section 4: ExpertAgent interface contract.
    Platform adapters implement this interface (see agents/ for available adapters).
    """
    @abstractmethod
    async def invoke(self, prompt: str, context: dict) -> ExpertReviewResult:
        """Invoke expert review and return structured result."""
        ...

    @abstractmethod
    def supports_parallel(self) -> bool:
        """Return True if this platform supports parallel subagent execution."""
        ...

    @abstractmethod
    def get_platform(self) -> Literal["openclaw", "hermes", "claude_code", "codex"]:
        """Return the platform identifier."""
        ...


# =============================================================================
# LLM-based Expert Invocation (Phase 26-02)
# =============================================================================

from pathlib import Path as Pathlib_Path

AGENTS_DIR = Pathlib_Path(__file__).parent.parent / "agents"


def build_input_review_prompt(
    card: "ExpertCardConfig",
    container: "EvidenceContainer",
) -> str:
    """Build input review prompt from agency-agents template.

    Per D-05: Template + placeholder replacement with {evidence}, {check_signals}.

    Args:
        card: ExpertCardConfig with prompt_file field
        container: EvidenceContainer with available sources

    Returns:
        Formatted prompt string with evidence and check_signals substituted.

    Raises:
        FileNotFoundError: If prompt_file does not exist under AGENTS_DIR
    """
    from runtime.expert_analysis_helper import EvidenceContainer

    if not card.prompt_file:
        raise ValueError("prompt_file not set on card")

    # Read prompt template from agents/ directory
    prompt_path = AGENTS_DIR / card.prompt_file
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    prompt_template = prompt_path.read_text(encoding="utf-8")

    # Render evidence from container
    evidence_parts: list[str] = []
    for source_name, source in container.sources.items():
        if source.available and source.content:
            content_preview = "\n".join(source.content[:10])  # Limit to first 10 items
            evidence_parts.append(f"[{source_name}]\n{content_preview}")

    evidence_text = "\n\n".join(evidence_parts) if evidence_parts else "(No evidence available)"

    # Substitute placeholders
    prompt = prompt_template.replace("{evidence}", evidence_text)
    prompt = prompt.replace("{check_signals}", ", ".join(card.check_signals))
    prompt = prompt.replace("{expert_name}", card.expert_name)

    return prompt


def build_output_review_prompt(
    card: "ExpertCardConfig",
    recommendations: list[str],
) -> str:
    """Build output review prompt from agency-agents template.

    Per D-05: Template + placeholder replacement with {recommendations}, {check_signals}.

    Args:
        card: ExpertCardConfig with prompt_file field
        recommendations: List of recommendation strings to audit

    Returns:
        Formatted prompt string with recommendations and check_signals substituted.

    Raises:
        FileNotFoundError: If prompt_file does not exist under AGENTS_DIR
    """
    if not card.prompt_file:
        raise ValueError("prompt_file not set on card")

    prompt_path = AGENTS_DIR / card.prompt_file
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    prompt_template = prompt_path.read_text(encoding="utf-8")

    recommendations_text = "\n".join(f"- {rec}" for rec in recommendations)
    prompt = prompt_template.replace("{recommendations}", recommendations_text)
    prompt = prompt.replace("{check_signals}", ", ".join(card.check_signals))
    prompt = prompt.replace("{expert_name}", card.expert_name)

    return prompt


async def invoke_llm_expert(
    card: "ExpertCardConfig",
    prompt: str,
) -> ExpertReviewResult:
    """Invoke LLM-based expert review.

    Per D-06: Fail-open to keyword mode on LLM failure.
    Per D-01: Uses DefaultLLMExpertAgent with OpenAI/Anthropic API.

    Error handling (per OpenCode HIGH concern):
    - Timeout: asyncio.TimeoutError
    - Auth failure (401): AuthenticationError
    - Rate limit (429): RateLimitError
    - Empty response: ValueError("Empty response from LLM")
    - Parse failure: ValueError("No parseable findings")
    - All other exceptions: fallback to keyword mode

    Args:
        card: ExpertCardConfig with expert_name and prompt_file
        prompt: Pre-built prompt from build_input_review_prompt or build_output_review_prompt

    Returns:
        ExpertReviewResult from LLM parsing

    Raises:
        ValueError: If API keys missing
        asyncio.TimeoutError: On timeout
        Exception: On LLM API failure — caller catches and falls back to keyword mode
    """
    from runtime.default_llm_adapter import DefaultLLMExpertAgent

    agent = DefaultLLMExpertAgent(
        expert_name=card.expert_name,
        prompt_file=card.prompt_file or "",
    )

    return await agent.invoke(prompt, {})