import asyncio
from typing import List, Dict, DefaultDict
from collections import defaultdict
from datetime import datetime, timedelta
from ..domain.interfaces import StateRepository
from ..domain.models import ToolCallRecord, CircuitState

class InMemoryStateRepository(StateRepository):
    def __init__(self):
        self._records: DefaultDict[str, List[ToolCallRecord]] = defaultdict(list)
        self._states: Dict[str, CircuitState] = {}
        self._state_change_times: Dict[str, datetime] = {}
        self._consecutive_failures: DefaultDict[str, int] = defaultdict(int)

    async def record_call(self, record: ToolCallRecord) -> None:
        self._records[record.tool_name].append(record)
        # Prune old records (optional optimization, maybe strictly not needed for MVP)
        
    async def get_recent_calls(self, tool_name: str, window_seconds: int) -> List[ToolCallRecord]:
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        return [
            r for r in self._records[tool_name] 
            if r.timestamp >= cutoff
        ]

    async def get_state(self, tool_name: str) -> CircuitState:
        return self._states.get(tool_name, CircuitState.CLOSED)

    async def set_state(self, tool_name: str, state: CircuitState) -> None:
        self._states[tool_name] = state
        self._state_change_times[tool_name] = datetime.now()

    async def get_last_state_change(self, tool_name: str) -> datetime | None:
        return self._state_change_times.get(tool_name)

    async def get_consecutive_failures(self, tool_name: str) -> int:
        return self._consecutive_failures[tool_name]
    
    async def increment_failures(self, tool_name: str) -> None:
        self._consecutive_failures[tool_name] += 1

    async def reset_failures(self, tool_name: str) -> None:
        self._consecutive_failures[tool_name] = 0
