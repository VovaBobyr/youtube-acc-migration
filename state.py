from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from config import settings
from logger import logger
from utils import load_json, save_json


ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)


@dataclass
class FailedEntry:
    channel_id: str
    reason: str


@dataclass
class MigrationState:
    input_file: str
    processed: List[str] = field(default_factory=list)
    failed: List[FailedEntry] = field(default_factory=list)
    last_updated: str = field(default_factory=_now_iso)

    @classmethod
    def load(cls, path: Path | None = None, input_file: str | None = None) -> "MigrationState":
        path = path or settings.migration_state_file
        raw = load_json(path)
        if not raw:
            if input_file is None:
                raise ValueError("input_file must be provided when creating a new MigrationState.")
            logger.info("No existing migration state found. Creating new state at %s", path)
            return cls(input_file=input_file)

        failed_entries = [
            FailedEntry(channel_id=e["channel_id"], reason=e.get("reason", "unknown"))
            for e in raw.get("failed", [])
        ]
        return cls(
            input_file=raw["input_file"],
            processed=list(raw.get("processed", [])),
            failed=failed_entries,
            last_updated=raw.get("last_updated", _now_iso()),
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["failed"] = [asdict(f) for f in self.failed]
        return data

    def save(self, path: Path | None = None) -> None:
        path = path or settings.migration_state_file
        self.last_updated = _now_iso()
        save_json(path, self.to_dict())
        logger.info("Saved migration state to %s", path)

    def mark_processed(self, channel_id: str) -> None:
        if channel_id not in self.processed:
            self.processed.append(channel_id)

    def mark_failed(self, channel_id: str, reason: str) -> None:
        self.failed = [f for f in self.failed if f.channel_id != channel_id]
        self.failed.append(FailedEntry(channel_id=channel_id, reason=reason))


__all__ = ["MigrationState", "FailedEntry"]

