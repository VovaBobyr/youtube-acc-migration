from __future__ import annotations

from pathlib import Path
from typing import Literal

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from config import settings
from logger import logger


AccountType = Literal["source", "target"]

# Separate scopes for least privilege
SOURCE_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
TARGET_SCOPES = ["https://www.googleapis.com/auth/youtube"]


def _get_token_path(account_type: AccountType) -> Path:
    if account_type == "source":
        return settings.source_token_file
    return settings.target_token_file


def _get_scopes(account_type: AccountType) -> list[str]:
    return SOURCE_SCOPES if account_type == "source" else TARGET_SCOPES


def get_credentials(account_type: AccountType, *, interactive: bool = True) -> Credentials:
    """Load or obtain OAuth2 credentials for the given account."""
    token_path = _get_token_path(account_type)
    scopes = _get_scopes(account_type)

    creds: Credentials | None = None
    if token_path.exists():
        logger.info("Loading cached %s account credentials from %s", account_type, token_path)
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)

    if creds and creds.expired and creds.refresh_token:
        logger.info("Refreshing expired %s account credentials.", account_type)
        creds.refresh(Request())

    if not creds or not creds.valid:
        if not interactive:
            raise RuntimeError(
                f"Credentials for {account_type} account are missing or invalid and "
                f"interactive auth is disabled."
            )

        logger.info("Starting OAuth flow for %s account.", account_type)
        if not settings.client_secrets_file.exists():
            raise FileNotFoundError(
                f"Client secrets file not found at {settings.client_secrets_file}. "
                "Please create OAuth 2.0 client credentials and update GOOGLE_API_CLIENT_SECRETS_FILE."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(settings.client_secrets_file),
            scopes=scopes,
        )
        creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")
        logger.info("Saved %s account credentials to %s", account_type, token_path)

    return creds


def clear_credentials(account_type: AccountType) -> None:
    """Delete stored credentials for the given account type, if present."""
    token_path = _get_token_path(account_type)
    if token_path.exists():
        token_path.unlink()
        logger.info("Deleted stored credentials for %s account at %s", account_type, token_path)


__all__ = ["AccountType", "get_credentials", "clear_credentials"]

