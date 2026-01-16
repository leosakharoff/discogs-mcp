"""
Discogs API Client for MCP Server
"""
import os
import logging
from typing import Any, Optional
import httpx

logger = logging.getLogger(__name__)

DISCOGS_API_BASE = "https://api.discogs.com"


class DiscogsClient:
    """Client for Discogs API interactions."""

    def __init__(self, token: str, user_agent: str = "DiscogsMCP/1.0"):
        self.token = token
        self.user_agent = user_agent
        self.headers = {
            "Authorization": f"Discogs token={token}",
            "User-Agent": user_agent,
        }

    async def _request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """Make an API request to Discogs."""
        url = f"{DISCOGS_API_BASE}{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def search(
        self,
        query: str = None,
        type: str = None,  # release, master, artist, label
        title: str = None,
        artist: str = None,
        label: str = None,
        genre: str = None,
        style: str = None,
        country: str = None,
        year: str = None,
        format: str = None,
        per_page: int = 10,
        page: int = 1,
    ) -> dict:
        """Search the Discogs database."""
        params = {"per_page": per_page, "page": page}
        if query:
            params["q"] = query
        if type:
            params["type"] = type
        if title:
            params["title"] = title
        if artist:
            params["artist"] = artist
        if label:
            params["label"] = label
        if genre:
            params["genre"] = genre
        if style:
            params["style"] = style
        if country:
            params["country"] = country
        if year:
            params["year"] = year
        if format:
            params["format"] = format

        return await self._request("GET", "/database/search", params)

    async def get_release(self, release_id: int, currency: str = None) -> dict:
        """Get a release by ID."""
        params = {}
        if currency:
            params["curr_abbr"] = currency
        return await self._request("GET", f"/releases/{release_id}", params)

    async def get_master_release(self, master_id: int) -> dict:
        """Get a master release by ID."""
        return await self._request("GET", f"/masters/{master_id}")

    async def get_master_release_versions(
        self,
        master_id: int,
        format: str = None,
        label: str = None,
        country: str = None,
        sort: str = "released",
        sort_order: str = "asc",
        per_page: int = 25,
        page: int = 1,
    ) -> dict:
        """Get all versions of a master release."""
        params = {
            "sort": sort,
            "sort_order": sort_order,
            "per_page": per_page,
            "page": page,
        }
        if format:
            params["format"] = format
        if label:
            params["label"] = label
        if country:
            params["country"] = country

        return await self._request("GET", f"/masters/{master_id}/versions", params)

    async def get_artist(self, artist_id: int) -> dict:
        """Get an artist by ID."""
        return await self._request("GET", f"/artists/{artist_id}")

    async def get_artist_releases(
        self,
        artist_id: int,
        sort: str = "year",
        sort_order: str = "asc",
        per_page: int = 25,
        page: int = 1,
    ) -> dict:
        """Get releases by an artist."""
        params = {
            "sort": sort,
            "sort_order": sort_order,
            "per_page": per_page,
            "page": page,
        }
        return await self._request("GET", f"/artists/{artist_id}/releases", params)

    async def get_label(self, label_id: int) -> dict:
        """Get a label by ID."""
        return await self._request("GET", f"/labels/{label_id}")

    async def get_label_releases(
        self,
        label_id: int,
        sort: str = "year",
        sort_order: str = "asc",
        per_page: int = 25,
        page: int = 1,
    ) -> dict:
        """Get releases from a label."""
        params = {
            "sort": sort,
            "sort_order": sort_order,
            "per_page": per_page,
            "page": page,
        }
        return await self._request("GET", f"/labels/{label_id}/releases", params)

    async def get_user_identity(self) -> dict:
        """Get the identity of the authenticated user."""
        return await self._request("GET", "/oauth/identity")

    async def get_user_collection_folders(self, username: str) -> dict:
        """Get a user's collection folders."""
        return await self._request("GET", f"/users/{username}/collection/folders")

    async def get_user_collection_items(
        self,
        username: str,
        folder_id: int = 0,
        sort: str = "added",
        sort_order: str = "desc",
        per_page: int = 25,
        page: int = 1,
    ) -> dict:
        """Get items from a user's collection folder."""
        params = {
            "sort": sort,
            "sort_order": sort_order,
            "per_page": per_page,
            "page": page,
        }
        return await self._request(
            "GET",
            f"/users/{username}/collection/folders/{folder_id}/releases",
            params
        )

    async def get_user_wantlist(
        self,
        username: str,
        per_page: int = 25,
        page: int = 1,
    ) -> dict:
        """Get a user's wantlist."""
        params = {"per_page": per_page, "page": page}
        return await self._request("GET", f"/users/{username}/wants", params)

    async def get_release_community_rating(self, release_id: int) -> dict:
        """Get the community rating for a release."""
        return await self._request("GET", f"/releases/{release_id}/rating")

    async def get_release_stats(self, release_id: int) -> dict:
        """Get marketplace stats for a release (haves, wants, price data)."""
        return await self._request("GET", f"/marketplace/stats/{release_id}")

    async def get_user_collection_value(self, username: str) -> dict:
        """Get the estimated value of a user's collection."""
        return await self._request("GET", f"/users/{username}/collection/value")

    async def get_user_profile(self, username: str) -> dict:
        """Get a user's profile information."""
        return await self._request("GET", f"/users/{username}")
