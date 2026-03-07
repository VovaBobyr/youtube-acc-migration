from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import settings


def _create_file_handler(log_path: Path) -> RotatingFileHandler:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    return handler


def _create_console_handler() -> logging.Handler:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    return handler


def get_logger(name: str | None = None) -> logging.Logger:
    """Return an application logger configured for console and file output."""
    logger_name = name or "youtube_subscription_migrator"
    logger = logging.getLogger(logger_name)

    if logger.handlers:
        # Already configured
        return logger

    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    log_file = settings.logs_dir / "app.log"
    logger.addHandler(_create_console_handler())
    logger.addHandler(_create_file_handler(log_file))
    logger.propagate = False

    return logger


logger = get_logger()

