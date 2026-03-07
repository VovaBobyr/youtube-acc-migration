from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, TypeVar

from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import settings
from logger import logger


T = TypeVar("T")


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def sleep_with_logging(seconds: float) -> None:
    if seconds <= 0:
        return
    logger.info("Sleeping for %.2f seconds to respect rate limits.", seconds)
    time.sleep(seconds)


def make_retryable(
    exceptions: tuple[type[BaseException], ...],
    *,
    max_attempts: int | None = None,
    max_delay: float | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator factory to wrap a function with exponential backoff retry."""

    attempts = max_attempts or settings.max_retry_attempts
    delay = max_delay or settings.max_delay_seconds

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @retry(
            retry=retry_if_exception_type(exceptions),
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(max=delay),
            reraise=True,
        )
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["load_json", "save_json", "sleep_with_logging", "make_retryable", "RetryError"]

