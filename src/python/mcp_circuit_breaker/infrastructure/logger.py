import sys

from loguru import logger

from .config import Settings


def configure_logger(settings: Settings) -> None:
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    # Enable file logging for debugging integration issues
    logger.add("/tmp/mcp_circuit_breaker.log", rotation="1 MB", level="DEBUG")
