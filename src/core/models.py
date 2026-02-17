"""
Core circuit breaker models - shared between MCP and Skills implementations.

This module contains pure data models with no external dependencies.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class CircuitState(str, Enum):
    """Circuit breaker state machine states."""

    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Trip triggered, blocking requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


@dataclass
class ToolCallRecord:
    """Record of a tool call for tracking and analysis."""

    tool_name: str
    timestamp: datetime
    args_hash: str  # Hash of arguments to detect exact duplicates
    error: Optional[str] = None

    @staticmethod
    def compute_hash(args: dict[str, Any]) -> str:
        """Compute a consistent hash of tool arguments."""
        import hashlib
        import json

        # Sort keys to ensure consistent hashing
        s = json.dumps(args, sort_keys=True, default=str)
        return hashlib.sha256(s.encode()).hexdigest()
