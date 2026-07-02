import json as json_module
import os
from typing import AsyncIterator

import httpx


class EventsProviderClient:
    """HTTP client for Events Provider API."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
        follow_redirects: bool = True,
    ):
        self.base_url = (base_url or os.getenv("EVENTS_PROVIDER_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("EVENTS_PROVIDER_API_KEY", "")
        self.timeout = timeout
        self.follow_redirects = follow_redirects

    def _headers(self) -> dict:
        return {"x-api-key": self.api_key}

    async def get_events(self, changed_at: str, cursor: str | None = None) -> dict:
        """Fetch a single page of events."""
        params = {"changed_at": changed_at}
        if cursor:
            params["cursor"] = cursor

        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=self.follow_redirects,
        ) as client:
            response = await client.get(
                f"{self.base_url}/api/events/",
                headers=self._headers(),
                params=params,
            )
            response.raise_for_status()
            return response.json()

    async def get_seats(self, event_id: str) -> list[str]:
        """Fetch available seats for an event."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/events/{event_id}/seats/",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()["seats"]

    async def register(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> str:
        """Register a participant. Returns ticket_id."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/events/{event_id}/register/",
                headers=self._headers(),
                json={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "seat": seat,
                },
            )
            response.raise_for_status()
            return response.json()["ticket_id"]

    async def unregister(self, event_id: str, ticket_id: str) -> bool:
        """Cancel a registration. Returns True on success."""
        headers = self._headers()
        headers["Content-Type"] = "application/json"

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.request(
                method="DELETE",
                url=f"{self.base_url}/api/events/{event_id}/unregister/",
                headers=headers,
                content=json_module.dumps({"ticket_id": ticket_id}),
            )
            response.raise_for_status()
            return response.json()["success"]


class EventsPaginator:
    """Async iterator over all events from the provider using cursor-based pagination."""

    def __init__(self, client: EventsProviderClient, changed_at: str = "2000-01-01"):
        self.client = client
        self.changed_at = changed_at

    async def __aiter__(self) -> AsyncIterator[dict]:
        cursor = None
        while True:
            page = await self.client.get_events(self.changed_at, cursor=cursor)
            for event in page["results"]:
                yield event
            if page["next"] is None:
                break
            # Extract cursor from next URL
            cursor = page["next"].split("cursor=")[-1]
