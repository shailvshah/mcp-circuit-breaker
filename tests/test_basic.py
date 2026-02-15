import pytest
import asyncio
from datetime import datetime
from mcp_circuit_breaker.domain.models import CircuitState, ToolCallRecord
from mcp_circuit_breaker.infrastructure.memory_repo import InMemoryStateRepository
from mcp_circuit_breaker.application.circuit_breaker import CircuitBreakerService
from mcp_circuit_breaker.infrastructure.config import Settings

@pytest.mark.asyncio
async def test_circuit_breaker_trips():
    repo = InMemoryStateRepository()
    # Mocking settings
    class MockSettings:
        cb_failure_threshold=2
        cb_window_seconds=60
        cb_max_requests_per_window=10
        downstream_command="echo"
        downstream_args=[]
        downstream_env={}
        
    settings = MockSettings()
    cb = CircuitBreakerService(repo, settings)
    
    tool_name = "test_tool"
    args = {"arg": "value"}
    
    # 1. First failure
    await cb.record_failure(tool_name, args, "Error 1")
    assert await repo.get_consecutive_failures(tool_name) == 1
    assert await repo.get_state(tool_name) != CircuitState.OPEN
    
    # 2. Second failure (Trips)
    await cb.record_failure(tool_name, args, "Error 2")
    assert await repo.get_consecutive_failures(tool_name) == 2
    assert await repo.get_state(tool_name) == CircuitState.OPEN
    
    # 3. Should be blocked
    can_exec = await cb.can_execute(tool_name, args)
    assert can_exec is False

@pytest.mark.asyncio
async def test_circuit_breaker_resets_on_success():
    repo = InMemoryStateRepository()
    class MockSettings:
        cb_failure_threshold=2
        cb_window_seconds=60
        cb_max_requests_per_window=10
        downstream_command="echo"
        downstream_args=[]
        downstream_env={}

    settings = MockSettings()
    cb = CircuitBreakerService(repo, settings)
    
    tool_name = "test_tool"
    args = {"arg": "value"}
    
    await cb.record_failure(tool_name, args, "Error 1")
    assert await repo.get_consecutive_failures(tool_name) == 1
    
    await cb.record_success(tool_name, args)
    assert await repo.get_consecutive_failures(tool_name) == 0
