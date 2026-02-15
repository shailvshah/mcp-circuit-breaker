from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Circuit Breaker Configuration
    cb_failure_threshold: int = 5
    cb_reset_timeout: int = 60
    cb_window_seconds: int = 60
    cb_max_requests_per_window: int = 10
    
    # Downstream MCP Server Configuration
    downstream_command: str
    downstream_args: List[str] = []
    downstream_env: Optional[dict] = None

    class Config:
        env_prefix = "" 
        env_file = ".env"
        extra = "ignore"
