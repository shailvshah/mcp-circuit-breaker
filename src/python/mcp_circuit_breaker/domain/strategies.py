"""
MCP-specific strategy implementations.

This module wraps core strategies with MCP-specific logging and integrations.
"""

from typing import Optional, cast

from core.strategies import (
    CircuitBreakerStrategy,
    StrategyContext,
)
from core.strategies import (
    CoolOffStrategy as CoreCoolOffStrategy,
)
from core.strategies import (
    SemanticStrategy as CoreSemanticStrategy,
)
from core.strategies import (
    StrictStrategy as CoreStrictStrategy,
)
from loguru import logger

# Re-export core types
__all__ = [
    "CircuitBreakerStrategy",
    "StrategyContext",
    "CoolOffStrategy",
    "SemanticStrategy",
    "StrictStrategy",
]


# MCP-specific wrappers with logging
class CoolOffStrategy(CoreCoolOffStrategy):
    """Cool-off strategy with MCP-specific logging."""

    async def should_block(self, context: StrategyContext) -> Optional[str]:
        result = cast(Optional[str], await super().should_block(context))
        if result:
            logger.warning(f"CoolOff strategy blocking {context.tool_name}: {result}")
        return result

    async def record_result(self, context: StrategyContext, is_success: bool) -> None:
        await super().record_result(context, is_success)
        if is_success:
            state = await context.repo.get_state(context.tool_name)
            if state.value == "HALF_OPEN":
                logger.info(f"Circuit for {context.tool_name} closed (recovered).")
        else:
            failures = await context.repo.get_consecutive_failures(context.tool_name)
            if failures >= context.settings.cb_failure_threshold:
                logger.error(
                    f"Circuit for {context.tool_name} TRIPPED after "
                    f"{failures} failures."
                )


class SemanticStrategy(CoreSemanticStrategy):
    """Semantic strategy with MCP-specific logging."""

    async def record_result(self, context: StrategyContext, is_success: bool) -> None:
        if not is_success and context.error:
            for pattern, action in context.settings.cb_semantic_patterns.items():
                import re

                if re.search(pattern, context.error, re.IGNORECASE):
                    logger.error(f"Semantic match '{pattern}'. Action: {action}")
        await super().record_result(context, is_success)


class StrictStrategy(CoreStrictStrategy):
    """Strict strategy - no additional MCP-specific behavior needed."""

    pass
