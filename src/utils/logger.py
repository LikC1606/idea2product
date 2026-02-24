"""Logging utilities for Idea2Product.

Provides a standardized logging setup with:
- Rich console output for interactive sessions
- Structured file logging with timestamps
- Correlation ID support (project_id, request_id) via contextvars
"""

import logging
import sys
import threading
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler

_correlation = threading.local()


def set_correlation(*, project_id: str = None, request_id: str = None):
    """Set correlation IDs for the current thread (visible in log output)."""
    if project_id is not None:
        _correlation.project_id = project_id
    if request_id is not None:
        _correlation.request_id = request_id


def clear_correlation():
    _correlation.project_id = None
    _correlation.request_id = None


class _CorrelationFilter(logging.Filter):
    """Injects correlation IDs into every log record."""

    def filter(self, record):
        record.project_id = getattr(_correlation, "project_id", None) or ""
        record.request_id = getattr(_correlation, "request_id", None) or ""
        return True


_INITIALIZED_LOGGERS: set = set()

_FILE_FORMAT = (
    "%(asctime)s [%(levelname)s] %(name)s"
    " [proj=%(project_id)s req=%(request_id)s]"
    " %(message)s"
)
_FILE_FORMAT_SHORT = "%(asctime)s [%(levelname)s] %(name)s %(message)s"


def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """Set up a logger with console and optional file handlers.

    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    if name in _INITIALIZED_LOGGERS:
        if log_file:
            _add_file_handler(logger, log_file)
        return logger
    _INITIALIZED_LOGGERS.add(name)

    logger.handlers = []
    logger.addFilter(_CorrelationFilter())

    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_path=False,
    )
    console_handler.setLevel(level)
    console_formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    if log_file:
        _add_file_handler(logger, log_file)

    return logger


def _add_file_handler(logger: logging.Logger, log_file: Path):
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.addFilter(_CorrelationFilter())
    file_formatter = logging.Formatter(_FILE_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with the given name.

    If the root 'idea2product' logger hasn't been set up yet, this creates
    a minimal configuration so that library-style modules that call
    ``get_logger(__name__)`` at import time still produce output.
    """
    logger = logging.getLogger(name)
    if not logger.handlers and not logging.getLogger().handlers:
        logger.addFilter(_CorrelationFilter())
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(_FILE_FORMAT_SHORT, datefmt="%H:%M:%S"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
