"""
Core circuit breaker logic - shared between MCP and Skills implementations.

This package contains pure strategy implementations, models, and validation
logic that can be used independently of the MCP protocol.
"""

from .models import CircuitState, ToolCallRecord
from .strategies import (
    CircuitBreakerStrategy,
    CoolOffStrategy,
    SemanticStrategy,
    StateRepository,
    StrategyContext,
    StrictStrategy,
)
from .validation import validate_pattern, validate_strategy_config

__all__ = [
    "CircuitState",
    "ToolCallRecord",
    "CircuitBreakerStrategy",
    "CoolOffStrategy",
    "SemanticStrategy",
    "StrictStrategy",
    "StrategyContext",
    "StateRepository",
    "validate_strategy_config",
    "validate_pattern",
]
