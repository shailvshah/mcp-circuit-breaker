from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from .models import CircuitState, ToolCallRecord


class StateRepository(ABC):
    @abstractmethod
    async def record_call(self, record: ToolCallRecord) -> None:
        """Record a tool call attempt."""
        pass

    @abstractmethod
    async def get_recent_calls(
        self, tool_name: str, window_seconds: int
    ) -> List[ToolCallRecord]:
        """Get calls for a tool within the last N seconds."""
        pass

    @abstractmethod
    async def get_state(self, tool_name: str) -> CircuitState:
        """Get current circuit state for a tool."""
        pass

    @abstractmethod
    async def set_state(self, tool_name: str, state: CircuitState) -> None:
        """Update circuit state for a tool."""
        pass

    @abstractmethod
    async def get_consecutive_failures(self, tool_name: str) -> int:
        """Get number of consecutive failures."""
        pass

    @abstractmethod
    async def increment_failures(self, tool_name: str) -> None:
        """Increment consecutive failure count."""
        pass

    @abstractmethod
    async def reset_failures(self, tool_name: str) -> None:
        """Reset consecutive failure count."""
        pass

    @abstractmethod
    async def get_last_state_change(self, tool_name: str) -> datetime | None:
        """Get timestamp of last state change."""
        pass
