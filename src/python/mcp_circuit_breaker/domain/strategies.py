import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Protocol

from loguru import logger

from ..infrastructure.config import Settings
from .interfaces import StateRepository
from .models import CircuitState


@dataclass
class StrategyContext:
    tool_name: str
    arguments: Dict[str, Any]
    settings: Settings
    repo: StateRepository
    error: Optional[str] = None


class CircuitBreakerStrategy(Protocol):
    """
    Interface for implementing different circuit breaker strategies.
    Strategies can block execution (pre-check) or update state based on results
    (post-check).
    """

    async def should_block(self, context: StrategyContext) -> Optional[str]:
        """
        Determines if the execution should be blocked.
        Returns a rejection message string if blocked, or None if allowed to proceed.
        """
        ...

    async def record_result(self, context: StrategyContext, is_success: bool) -> None:
        """
        Updates the strategy's internal state based on the execution result.
        """
        ...


class CoolOffStrategy:
    """
    The standard time-based circuit breaker.
    Trips after N failures, opens for T seconds, then Half-Open.
    """

    async def should_block(self, context: StrategyContext) -> Optional[str]:
        state = await context.repo.get_state(context.tool_name)

        if state == CircuitState.OPEN:
            last_change = await context.repo.get_last_state_change(context.tool_name)
            if last_change:
                elapsed = (datetime.now() - last_change).total_seconds()
                if elapsed > context.settings.cb_reset_timeout:
                    logger.info(
                        f"CoolOff: Reset timeout passed ({elapsed}s). "
                        "Transitioning to HALF_OPEN."
                    )
                    await context.repo.set_state(
                        context.tool_name, CircuitState.HALF_OPEN
                    )
                    return None  # Allow trial

            return (
                "I've paused this tool temporarily because it has failed multiple "
                "times in a row. Let's wait a moment before trying again to avoid "
                "overloading the system."
            )

        # Check Rate Limit / Sliding Window
        recent_calls = await context.repo.get_recent_calls(
            context.tool_name, context.settings.cb_window_seconds
        )
        if len(recent_calls) >= context.settings.cb_max_requests_per_window:
            logger.warning(f"Rate limit exceeded for {context.tool_name}")
            return (
                "I'm executing this tool too quickly. I need to slow down to "
                "respect the rate limits."
            )

        return None

    async def record_result(self, context: StrategyContext, is_success: bool) -> None:
        if is_success:
            state = await context.repo.get_state(context.tool_name)
            if state == CircuitState.HALF_OPEN:
                await context.repo.set_state(context.tool_name, CircuitState.CLOSED)
                await context.repo.reset_failures(context.tool_name)
                logger.info(f"Circuit for {context.tool_name} closed (recovered).")
            await context.repo.reset_failures(context.tool_name)
        else:
            await context.repo.increment_failures(context.tool_name)
            failures = await context.repo.get_consecutive_failures(context.tool_name)
            if failures >= context.settings.cb_failure_threshold:
                current_state = await context.repo.get_state(context.tool_name)
                if current_state != CircuitState.OPEN:
                    await context.repo.set_state(context.tool_name, CircuitState.OPEN)
                    logger.error(
                        f"Circuit for {context.tool_name} TRIPPED after "
                        f"{failures} failures."
                    )


class SemanticStrategy:
    """
    Analyzes error messages to determine if they are fatal.
    """

    async def should_block(self, context: StrategyContext) -> Optional[str]:
        # Semantic checks are usually post-failure, unless we persistence "Fatal" state.
        # For now, we assume if it tripped via Semantic, it stays tripped until manual
        # reset or very long timeout.
        # We can reuse the OPEN state but maybe with a special flag?
        # For MVP, let's treat it as an extension of standard state but triggered
        # differently. This simplifies the logic significantly.
        # Actually, if we want separate logic, we should check a specific
        # "Semantic Block" state.
        # Simpler: If error matches "Fatal", we set a special key in repo or just trip
        # the circuit immediately.
        return None

    async def record_result(self, context: StrategyContext, is_success: bool) -> None:
        if not is_success and context.error:
            for pattern, action in context.settings.cb_semantic_patterns.items():
                if re.search(pattern, context.error, re.IGNORECASE):
                    logger.error(f"Semantic match '{pattern}'. Action: {action}")
                    # If action is "block", trip the circuit immediately
                    if action.lower() == "block":
                        await context.repo.set_state(
                            context.tool_name, CircuitState.OPEN
                        )
                        # Maybe set a very long timeout? Or just rely on standard Open?
                        # For now, standard Open.


class StrictStrategy:
    """
    Firewall: Blocks based on tool name or argument patterns.
    """

    async def should_block(self, context: StrategyContext) -> Optional[str]:
        # Check Tool Name against Blocklist
        for pattern in context.settings.cb_strict_blocklist:
            if re.match(pattern, context.tool_name):
                return (
                    f"I can't execute the '{context.tool_name}' tool because "
                    "it's restricted by your current security policy."
                )
        return None

    async def record_result(self, context: StrategyContext, is_success: bool) -> None:
        pass
