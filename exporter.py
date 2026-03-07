from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from config import settings
from logger import logger
from utils import save_json
from youtube_client import YouTubeClient


def export_subscriptions(output_path: Path | None = None) -> Path:
    """Export all source account subscriptions to JSON."""
    output_path = output_path or settings.default_export_file
    client = YouTubeClient(account_type="source")
    subscriptions: List[Dict[str, str]] = client.list_all_subscriptions()

    save_json(output_path, subscriptions)
    logger.info("Exported %d subscriptions to %s", len(subscriptions), output_path)
    return output_path


__all__ = ["export_subscriptions"]

