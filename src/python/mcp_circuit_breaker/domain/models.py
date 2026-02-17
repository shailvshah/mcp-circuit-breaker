"""
Domain models for MCP Circuit Breaker.

This module re-exports core models for backward compatibility.
"""

from core.models import CircuitState, ToolCallRecord

__all__ = ["CircuitState", "ToolCallRecord"]
