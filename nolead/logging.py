import logging
import sys
from enum import Enum
from typing import Optional


class LogLevel(Enum):
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG


# Default logger configuration
_logger = logging.getLogger("nolead")
_handler = logging.StreamHandler(sys.stdout)
_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)
_logger.setLevel(logging.INFO)


def configure_logging(
    level: LogLevel = LogLevel.INFO,
    log_file: Optional[str] = None,
    format_str: Optional[str] = None,
) -> None:
    """Configure the logging for the nolead library.

    Args:
        level: The log level to use
        log_file: Optional file to log to (in addition to stdout)
        format_str: Optional custom format string for log messages
    """
    global _logger, _handler, _formatter

    # Set log level
    _logger.setLevel(level.value)

    # Change formatter if requested
    if format_str:
        _formatter = logging.Formatter(format_str)
        _handler.setFormatter(_formatter)

    # Add file handler if requested
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(_formatter)
        _logger.addHandler(file_handler)


def get_logger() -> logging.Logger:
    """Get the nolead logger instance."""
    return _logger
