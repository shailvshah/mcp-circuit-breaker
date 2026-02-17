from unittest.mock import AsyncMock

import pytest
from mcp_circuit_breaker.domain.models import CircuitState
from mcp_circuit_breaker.domain.strategies import (
    SemanticStrategy,
    StrategyContext,
    StrictStrategy,
)
from mcp_circuit_breaker.infrastructure.config import Settings


# --- Strict Strategy Tests ---
@pytest.mark.asyncio
async def test_strict_strategy_allows_safe_tools():
    settings = Settings(
        downstream_command="echo", cb_strict_blocklist=[r"^delete_.*", r"^drop_.*"]
    )
    repo = AsyncMock()
    strategy = StrictStrategy()

    context = StrategyContext(
        tool_name="read_file", arguments={}, settings=settings, repo=repo
    )

    assert await strategy.should_block(context) is None


@pytest.mark.asyncio
async def test_strict_strategy_blocks_dangerous_tools():
    settings = Settings(downstream_command="echo", cb_strict_blocklist=[r"^delete_.*"])
    repo = AsyncMock()
    strategy = StrictStrategy()

    context = StrategyContext(
        tool_name="delete_database", arguments={}, settings=settings, repo=repo
    )

    result = await strategy.should_block(context)
    assert result is not None
    assert "restricted by your current security policy" in result


# --- Semantic Strategy Tests ---
@pytest.mark.asyncio
async def test_semantic_strategy_ignores_success():
    settings = Settings(
        downstream_command="echo", cb_semantic_patterns={r"Rate limit": "block"}
    )
    repo = AsyncMock()
    strategy = SemanticStrategy()

    context = StrategyContext(
        tool_name="api_call", arguments={}, settings=settings, repo=repo
    )

    # verify it does nothing on success
    await strategy.record_result(context, is_success=True)
    repo.set_state.assert_not_called()


@pytest.mark.asyncio
async def test_semantic_strategy_trips_on_pattern_match():
    settings = Settings(
        downstream_command="echo",
        cb_semantic_patterns={r"Rate limit exceeded": "block"},
    )
    repo = AsyncMock()
    strategy = SemanticStrategy()

    context = StrategyContext(
        tool_name="api_call",
        arguments={},
        settings=settings,
        repo=repo,
        error="Error 429: Rate limit exceeded. Please try again later.",
    )

    await strategy.record_result(context, is_success=False)

    # Should trip to OPEN immediately
    repo.set_state.assert_called_with("api_call", CircuitState.OPEN)


@pytest.mark.asyncio
async def test_semantic_strategy_ignores_unmatched_error():
    settings = Settings(
        downstream_command="echo", cb_semantic_patterns={r"Fatal Error": "block"}
    )
    repo = AsyncMock()
    strategy = SemanticStrategy()

    context = StrategyContext(
        tool_name="api_call",
        arguments={},
        settings=settings,
        repo=repo,
        error="Just a normal typo",
    )

    await strategy.record_result(context, is_success=False)
    repo.set_state.assert_not_called()
