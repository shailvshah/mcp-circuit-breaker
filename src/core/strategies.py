"""
Core circuit breaker strategies - shared between MCP and Skills implementations.

This module contains pure strategy logic with minimal dependencies.
For MCP-specific integration, see mcp_circuit_breaker.domain.strategies.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Protocol

from .models import CircuitState


# Abstract interfaces for dependency injection
class StateRepository(Protocol):
    """Interface for state persistence (injected by implementation)."""

    async def get_state(self, tool_name: str) -> CircuitState: ...

    async def set_state(self, tool_name: str, state: CircuitState) -> None: ...

    async def get_last_state_change(self, tool_name: str) -> Optional[datetime]: ...

    async def get_recent_calls(
        self, tool_name: str, window_seconds: int
    ) -> list[Any]: ...

    async def increment_failures(self, tool_name: str) -> None: ...

    async def get_consecutive_failures(self, tool_name: str) -> int: ...

    async def reset_failures(self, tool_name: str) -> None: ...


class Settings(Protocol):
    """Interface for configuration (injected by implementation)."""

    cb_failure_threshold: int
    cb_reset_timeout: int
    cb_window_seconds: int
    cb_max_requests_per_window: int
    cb_semantic_patterns: Dict[str, str]
    cb_strict_blocklist: list[str]


@dataclass
class StrategyContext:
    """Context passed to strategies for decision making."""

    tool_name: str
    arguments: Dict[str, Any]
    settings: Settings
    repo: StateRepository
    error: Optional[str] = None


class CircuitBreakerStrategy(Protocol):
    """
    Interface for implementing different circuit breaker strategies.
    Strategies can block execution (pre-check) or update state based on
    results (post-check).
    """

    async def should_block(self, context: StrategyContext) -> Optional[str]:
        """
        Determines if the execution should be blocked.
        Returns a rejection message string if blocked, or None if allowed.
        """
        ...

    async def record_result(self, context: StrategyContext, is_success: bool) -> None:
        """Updates the strategy's internal state based on execution result."""
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
                    await context.repo.set_state(
                        context.tool_name, CircuitState.HALF_OPEN
                    )
                    return None  # Allow trial

            return (
                "I've paused this tool temporarily because it has failed "
                "multiple times in a row. Let's wait a moment before trying "
                "again to avoid overloading the system."
            )

        # Check Rate Limit / Sliding Window
        recent_calls = await context.repo.get_recent_calls(
            context.tool_name, context.settings.cb_window_seconds
        )
        if len(recent_calls) >= context.settings.cb_max_requests_per_window:
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
            await context.repo.reset_failures(context.tool_name)
        else:
            await context.repo.increment_failures(context.tool_name)
            failures = await context.repo.get_consecutive_failures(context.tool_name)
            if failures >= context.settings.cb_failure_threshold:
                current_state = await context.repo.get_state(context.tool_name)
                if current_state != CircuitState.OPEN:
                    await context.repo.set_state(context.tool_name, CircuitState.OPEN)


class SemanticStrategy:
    """Analyzes error messages to determine if they are fatal."""

    async def should_block(self, context: StrategyContext) -> Optional[str]:
        # Semantic checks are usually post-failure
        # For MVP, we check state after error analysis in record_result
        return None

    async def record_result(self, context: StrategyContext, is_success: bool) -> None:
        if not is_success and context.error:
            for pattern, action in context.settings.cb_semantic_patterns.items():
                if re.search(pattern, context.error, re.IGNORECASE):
                    # If action is "block", trip the circuit immediately
                    if action.lower() == "block":
                        await context.repo.set_state(
                            context.tool_name, CircuitState.OPEN
                        )


class StrictStrategy:
    """Firewall: Blocks based on tool name or argument patterns."""

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
        pass  # Strict strategy doesn't update state
