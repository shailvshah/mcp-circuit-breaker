from datetime import datetime
from typing import Any, Dict, List

from loguru import logger

from ..domain.interfaces import StateRepository
from ..domain.models import ToolCallRecord
from ..domain.strategies import (
    CircuitBreakerStrategy,
    CoolOffStrategy,
    SemanticStrategy,
    StrategyContext,
    StrictStrategy,
)
from ..infrastructure.config import Settings


class CircuitBreakerService:
    def __init__(self, repository: StateRepository, settings: Settings):
        self.repo = repository
        self.settings = settings
        self.strategies: List[CircuitBreakerStrategy] = []
        self._initialize_strategies()

    def _initialize_strategies(self) -> None:
        strategy_map: Dict[str, CircuitBreakerStrategy] = {
            "cool-off": CoolOffStrategy(),
            "semantic": SemanticStrategy(),
            "strict": StrictStrategy(),
        }

        for name in self.settings.cb_strategies:
            if name in strategy_map:
                self.strategies.append(strategy_map[name])
                logger.info(f"Initialized strategy: {name}")
            else:
                logger.warning(f"Unknown strategy configured: {name}")

    async def can_execute(self, tool_name: str, args: Dict[str, Any]) -> bool:
        """
        Determines if a tool execution should be allowed by consulting
        the strategy chain.
        """
        context = StrategyContext(
            tool_name=tool_name, arguments=args, settings=self.settings, repo=self.repo
        )

        for strategy in self.strategies:
            block_reason = await strategy.should_block(context)
            if block_reason:
                logger.warning(
                    f"Strategy {type(strategy).__name__} blocked {tool_name}: "
                    f"{block_reason}"
                )
                # We could potentially return the reason string to be used
                # in the response. But the interface currently returns bool.
                # For now, we log it. The ProxyService handles the
                # generic message, but maybe eventually we want to pass this up.
                return False

        return True

    async def record_success(self, tool_name: str, args: Dict[str, Any]) -> None:
        context = StrategyContext(
            tool_name=tool_name, arguments=args, settings=self.settings, repo=self.repo
        )

        record = ToolCallRecord(
            tool_name=tool_name,
            timestamp=datetime.now(),
            args_hash=ToolCallRecord.compute_hash(args),
            error=None,
        )
        await self.repo.record_call(record)

        for strategy in self.strategies:
            await strategy.record_result(context, is_success=True)

    async def record_failure(
        self, tool_name: str, args: Dict[str, Any], error_msg: str
    ) -> None:
        context = StrategyContext(
            tool_name=tool_name,
            arguments=args,
            settings=self.settings,
            repo=self.repo,
            error=error_msg,
        )

        record = ToolCallRecord(
            tool_name=tool_name,
            timestamp=datetime.now(),
            args_hash=ToolCallRecord.compute_hash(args),
            error=error_msg,
        )
        await self.repo.record_call(record)

        for strategy in self.strategies:
            await strategy.record_result(context, is_success=False)
