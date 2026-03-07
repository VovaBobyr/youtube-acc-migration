from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from googleapiclient.errors import HttpError

from config import settings
from logger import logger
from state import MigrationState
from utils import RetryError, load_json, save_json, sleep_with_logging
from youtube_client import YouTubeClient


@dataclass
class MigrationStats:
    total: int = 0
    already_subscribed: int = 0
    newly_subscribed: int = 0
    failed: int = 0
    skipped: int = 0


def _load_subscriptions(input_path: Path) -> List[Dict[str, str]]:
    data = load_json(input_path)
    if not isinstance(data, list):
        raise ValueError(f"Invalid input file format: {input_path}")
    return data


def _write_summary_report(
    stats: MigrationStats,
    *,
    state: MigrationState,
    output_path: Optional[Path] = None,
) -> Path:
    output_path = output_path or settings.summary_report_file
    summary = {
        "input_file": state.input_file,
        "total": stats.total,
        "already_subscribed": stats.already_subscribed,
        "newly_subscribed": stats.newly_subscribed,
        "failed": stats.failed,
        "skipped": stats.skipped,
        "state_file": str(settings.migration_state_file),
    }
    save_json(output_path, summary)
    logger.info("Wrote summary report to %s", output_path)
    return output_path


def migrate_subscriptions(
    input_path: Path,
    *,
    delay_seconds: float | None = None,
    dry_run: bool = False,
    resume: bool = True,
    limit: Optional[int] = None,
    retry_failed_only: bool = False,
) -> None:
    """Migrate subscriptions from JSON file to target account."""
    delay_seconds = delay_seconds if delay_seconds is not None else settings.default_delay_seconds
    input_path = input_path.resolve()

    # Load subscriptions
    subscriptions = _load_subscriptions(input_path)

    # Load or create state
    state = MigrationState.load(
        input_file=str(input_path), path=settings.migration_state_file if resume else None
    )

    client = YouTubeClient(account_type="target")
    stats = MigrationStats(total=len(subscriptions))

    logger.info(
        "Starting migration: %d subscriptions, delay=%.2fs, dry_run=%s, resume=%s, limit=%s, retry_failed_only=%s",
        len(subscriptions),
        delay_seconds,
        dry_run,
        resume,
        str(limit) if limit is not None else "none",
        retry_failed_only,
    )

    processed_count = 0

    failed_ids_to_retry = {f.channel_id for f in state.failed} if retry_failed_only else set()

    for entry in subscriptions:
        channel_id = entry.get("channel_id")
        title = entry.get("title", "")

        if not channel_id:
            logger.warning("Skipping entry without channel_id: %s", entry)
            stats.skipped += 1
            continue

        if limit is not None and processed_count >= limit:
            logger.info("Reached processing limit (%d). Stopping.", limit)
            break

        if retry_failed_only and channel_id not in failed_ids_to_retry:
            stats.skipped += 1
            continue

        if channel_id in state.processed and not retry_failed_only:
            logger.debug("Skipping already processed channel %s (%s).", channel_id, title)
            stats.skipped += 1
            continue

        logger.info("Processing channel %s (%s)", channel_id, title)

        try:
            if client.is_already_subscribed(channel_id):
                logger.info(
                    "Target account already subscribed to %s (%s). Skipping.", channel_id, title
                )
                stats.already_subscribed += 1
                state.mark_processed(channel_id)
                state.save()
                processed_count += 1
                continue

            if dry_run:
                logger.info(
                    "[DRY RUN] Would subscribe target account to %s (%s).", channel_id, title
                )
                stats.newly_subscribed += 1
                state.mark_processed(channel_id)
                state.save()
                processed_count += 1
                continue

            try:
                client.subscribe_to_channel(channel_id)
                logger.info("Subscribed target account to %s (%s).", channel_id, title)
                stats.newly_subscribed += 1
                state.mark_processed(channel_id)
            except RetryError as e:
                reason = f"retry_exhausted: {e}"
                logger.error("Failed to subscribe to %s due to retries exhausted: %s", channel_id, e)
                state.mark_failed(channel_id, reason)
                stats.failed += 1
            except HttpError as e:
                reason = _extract_http_error_reason(e)
                logger.error(
                    "Failed to subscribe to %s (%s). Reason: %s", channel_id, title, reason
                )
                state.mark_failed(channel_id, reason)
                stats.failed += 1

            state.save()
            processed_count += 1

            # Rate limiting delay between write operations
            if not dry_run:
                sleep_with_logging(delay_seconds)

        except HttpError as e:
            reason = _extract_http_error_reason(e)
            logger.error(
                "Error while processing channel %s (%s). Reason: %s", channel_id, title, reason
            )
            state.mark_failed(channel_id, reason)
            stats.failed += 1
            state.save()

    logger.info(
        "Migration completed. total=%d, already_subscribed=%d, newly_subscribed=%d, "
        "failed=%d, skipped=%d",
        stats.total,
        stats.already_subscribed,
        stats.newly_subscribed,
        stats.failed,
        stats.skipped,
    )

    _write_summary_report(stats, state=state)


def _extract_http_error_reason(error: HttpError) -> str:
    try:
        error_content = error.error_details if hasattr(error, "error_details") else None
        if getattr(error, "resp", None) and hasattr(error, "content"):
            # Fallback: attempt to decode JSON error body
            import json

            data = json.loads(error.content.decode("utf-8"))
            return data.get("error", {}).get("errors", [{}])[0].get("reason", str(error))
        if error_content:
            return str(error_content)
    except Exception:  # noqa: BLE001
        pass
    return str(error)


__all__ = ["migrate_subscriptions"]

