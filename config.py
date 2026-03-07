from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent

# Load .env if present (expected to live in the project root)
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Application configuration loaded from environment variables with sane defaults."""

    # Paths
    base_dir: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    tokens_dir: Path = PROJECT_ROOT / "tokens"
    logs_dir: Path = PROJECT_ROOT / "logs"

    # Google / YouTube API
    client_secrets_file: Path = Path(
        os.getenv("GOOGLE_API_CLIENT_SECRETS_FILE", PROJECT_ROOT / "credentials.json")
    )

    # OAuth token filenames for source and target accounts
    source_token_file: Path = tokens_dir / os.getenv("SOURCE_TOKEN_FILENAME", "source_token.json")
    target_token_file: Path = tokens_dir / os.getenv("TARGET_TOKEN_FILENAME", "target_token.json")

    # Migration state and reports
    default_export_file: Path = data_dir / os.getenv(
        "DEFAULT_EXPORT_FILENAME", "source_subscriptions.json"
    )
    migration_state_file: Path = data_dir / os.getenv(
        "MIGRATION_STATE_FILENAME", "migration_state.json"
    )
    summary_report_file: Path = data_dir / os.getenv(
        "SUMMARY_REPORT_FILENAME", "migration_summary.json"
    )

    # Rate limiting and retries
    default_delay_seconds: float = float(os.getenv("DEFAULT_DELAY_SECONDS", "2.0"))
    max_delay_seconds: float = float(os.getenv("MAX_DELAY_SECONDS", "30.0"))
    max_retry_attempts: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "5"))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()

# Ensure important directories exist at import time for convenience
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.tokens_dir.mkdir(parents=True, exist_ok=True)
settings.logs_dir.mkdir(parents=True, exist_ok=True)

