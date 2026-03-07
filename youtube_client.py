from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError

from auth import AccountType, get_credentials
from logger import logger
from utils import make_retryable


RetryableHttpError = HttpError


class YouTubeClient:
    """Thin wrapper around the YouTube Data API v3."""

    def __init__(self, account_type: AccountType) -> None:
        creds = get_credentials(account_type)
        self.service: Resource = build("youtube", "v3", credentials=creds)
        self.account_type = account_type
        logger.info("Initialized YouTube client for %s account.", account_type)

    @make_retryable((RetryableHttpError,))
    def _subscriptions_list(
        self,
        *,
        mine: bool = True,
        page_token: Optional[str] = None,
        max_results: int = 50,
        for_channel_id: Optional[str] = None,
        part: str = "snippet",
    ) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "part": part,
            "maxResults": max_results,
        }
        if mine:
            kwargs["mine"] = True
        if page_token:
            kwargs["pageToken"] = page_token
        if for_channel_id:
            kwargs["forChannelId"] = for_channel_id

        request = self.service.subscriptions().list(**kwargs)
        return request.execute()

    @make_retryable((RetryableHttpError,))
    def _subscriptions_insert(self, *, channel_id: str) -> Dict[str, Any]:
        body = {
            "snippet": {
                "resourceId": {
                    "kind": "youtube#channel",
                    "channelId": channel_id,
                }
            }
        }
        request = self.service.subscriptions().insert(part="snippet", body=body)
        return request.execute()

    def list_all_subscriptions(self) -> List[Dict[str, str]]:
        """Return all channel subscriptions as a list of dicts with channel_id and title."""
        logger.info("Fetching subscriptions for %s account.", self.account_type)
        items: List[Dict[str, str]] = []
        page_token: Optional[str] = None

        while True:
            try:
                response = self._subscriptions_list(
                    mine=True,
                    page_token=page_token,
                    max_results=50,
                    part="snippet",
                )
            except HttpError as e:
                logger.error("Error fetching subscriptions: %s", e)
                raise

            for sub in response.get("items", []):
                snippet = sub.get("snippet", {})
                resource = snippet.get("resourceId", {})
                if resource.get("kind") != "youtube#channel":
                    continue
                channel_id = resource.get("channelId")
                title = snippet.get("title", "")
                if channel_id:
                    items.append({"channel_id": channel_id, "title": title})

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        logger.info("Fetched %d subscriptions.", len(items))
        return items

    def is_already_subscribed(self, channel_id: str) -> bool:
        """Check if current account is already subscribed to the given channel."""
        try:
            response = self._subscriptions_list(
                mine=True,
                for_channel_id=channel_id,
                max_results=1,
                part="id",
            )
        except HttpError as e:
            logger.error("Error checking subscription for %s: %s", channel_id, e)
            raise

        return bool(response.get("items"))

    def subscribe_to_channel(self, channel_id: str) -> Dict[str, Any]:
        """Subscribe current account to the given channel."""
        logger.debug("Subscribing to channel %s", channel_id)
        return self._subscriptions_insert(channel_id=channel_id)


__all__ = ["YouTubeClient"]

