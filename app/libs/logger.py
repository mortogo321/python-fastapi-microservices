import logging
import sys

from pythonjsonlogger.json import JsonFormatter

from app.libs.config import settings


def setup_logger(name: str) -> logging.Logger:
    """Configure structured JSON logging (idempotent under reload)."""
    logger = logging.getLogger(name)
    logger.setLevel(settings.log_level)
    logger.propagate = False

    # Remove existing handlers (uvicorn --reload re-imports modules)
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(settings.log_level)

    # JSON formatter for structured logging
    formatter = JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d",
        rename_fields={"levelname": "level", "asctime": "timestamp", "pathname": "file"},
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger
