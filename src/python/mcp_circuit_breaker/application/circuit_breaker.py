from datetime import datetime
from typing import Any, Dict
from ..domain.interfaces import StateRepository
from ..domain.models import CircuitState, ToolCallRecord
from ..infrastructure.config import Settings
from loguru import logger

class CircuitBreakerService:
    def __init__(self, repository: StateRepository, settings: Settings):
        self.repo = repository
        self.settings = settings

    async def can_execute(self, tool_name: str, args: Dict[str, Any]) -> bool:
        """
        Determines if a tool execution should be allowed.
        Raises specific exceptions if blocked to provide feedback to LLM.
        """
        state = await self.repo.get_state(tool_name)
        
        if state == CircuitState.OPEN:
             last_change = await self.repo.get_last_state_change(tool_name)
             if last_change:
                 from datetime import datetime, timedelta
                 elapsed = (datetime.now() - last_change).total_seconds()
                 if elapsed > self.settings.cb_reset_timeout:
                     logger.info(f"Circuit reset timeout passed ({elapsed}s > {self.settings.cb_reset_timeout}s). Transitioning to HALF_OPEN.")
                     await self.repo.set_state(tool_name, CircuitState.HALF_OPEN)
                     return True
             
             return False

        # Check Rate Limit / Sliding Window
        recent_calls = await self.repo.get_recent_calls(tool_name, self.settings.cb_window_seconds)
        if len(recent_calls) >= self.settings.cb_max_requests_per_window:
            logger.warning(f"Rate limit exceeded for {tool_name}")
            return False

        # Check for exact duplicate loops (same args repeatedly)
        args_hash = ToolCallRecord.compute_hash(args)
        # Get last N calls
        if recent_calls:
            # Simple check: is the last call exactly the same?
            if recent_calls[-1].args_hash == args_hash:
                 # Start counting duplicates? 
                 # For MVP, let's just rely on failure count or rate limit.
                 pass

        return True

    async def record_success(self, tool_name: str, args: Dict[str, Any]):
        record = ToolCallRecord(
            tool_name=tool_name,
            timestamp=datetime.now(),
            args_hash=ToolCallRecord.compute_hash(args),
            error=None
        )
        await self.repo.record_call(record)
        
        state = await self.repo.get_state(tool_name)
        if state == CircuitState.HALF_OPEN:
            await self.repo.set_state(tool_name, CircuitState.CLOSED)
            await self.repo.reset_failures(tool_name)
            logger.info(f"Circuit for {tool_name} closed (recovered).")
        
        # If CLOSED, we might want to reset failure count on success?
        # Usually yes, consecutive failures means *consecutive*.
        await self.repo.reset_failures(tool_name)

    async def record_failure(self, tool_name: str, args: Dict[str, Any], error_msg: str):
        record = ToolCallRecord(
            tool_name=tool_name,
            timestamp=datetime.now(),
            args_hash=ToolCallRecord.compute_hash(args),
            error=error_msg
        )
        await self.repo.record_call(record)
        await self.repo.increment_failures(tool_name)
        
        failures = await self.repo.get_consecutive_failures(tool_name)
        if failures >= self.settings.cb_failure_threshold:
            current_state = await self.repo.get_state(tool_name)
            if current_state != CircuitState.OPEN:
                await self.repo.set_state(tool_name, CircuitState.OPEN)
                logger.error(f"Circuit for {tool_name} TRIPPED after {failures} failures.")
