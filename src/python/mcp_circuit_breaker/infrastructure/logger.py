import sys
from loguru import logger
from .config import Settings

def configure_logger(settings: Settings):
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    # You could add file logging here if needed based on settings
    # logger.add("circuit_breaker.log", rotation="10 MB")
