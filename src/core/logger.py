"""Logging configuration for Trudy Telegram system."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from src.core.config import LoggingConfig


def setup_logging(config: Optional[LoggingConfig] = None) -> logging.Logger:
    """Setup structured logging with console and file handlers.

    Args:
        config: Logging configuration. If None, uses defaults.

    Returns:
        Configured logger instance
    """
    if config is None:
        config = LoggingConfig()

    # Create logger
    logger = logging.getLogger("trudy")
    logger.setLevel(getattr(logging, config.level))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler with Rich formatting
    console = Console()
    console_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        show_time=True,
        show_path=False,
    )
    console_handler.setLevel(getattr(logging, config.level))
    console_formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    log_file = Path(config.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Error file handler with rotation
    error_file = Path(config.error_file)
    error_file.parent.mkdir(parents=True, exist_ok=True)

    error_handler = RotatingFileHandler(
        filename=error_file,
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)  # Only errors and above
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    logger.info("Logging system initialized")
    return logger


def get_logger(name: str = "trudy") -> logging.Logger:
    """Get logger instance by name.

    Args:
        name: Logger name (defaults to 'trudy')

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
