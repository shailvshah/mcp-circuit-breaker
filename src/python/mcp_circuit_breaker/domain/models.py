from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class CircuitState(str, Enum):
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Trip triggered, blocking requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


@dataclass
class ToolCallRecord:
    tool_name: str
    timestamp: datetime
    args_hash: str  # Hash of arguments to detect exact duplicates
    error: Optional[str] = None

    @staticmethod
    def compute_hash(args: dict[str, Any]) -> str:
        import hashlib
        import json

        # Sort keys to ensure consistent hashing
        s = json.dumps(args, sort_keys=True, default=str)
        return hashlib.sha256(s.encode()).hexdigest()
