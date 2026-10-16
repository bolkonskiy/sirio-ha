"""WinET REST API client for Sirio pump controllers."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import SOFT_START_REGISTER_INDEX

_LOGGER = logging.getLogger(__name__)


class SirioApiError(Exception):
    """Base API error."""


class SirioApiConnectionError(SirioApiError):
    """Connection or transport error."""


class SirioApi:
    """Async client for Sirio / WinET ajax register endpoints."""

    def __init__(self, host: str, session: aiohttp.ClientSession) -> None:
        host = host.strip().removeprefix("http://").removeprefix("https://").rstrip("/")
        self._base_url = f"http://{host}"
        self._session = session

    @property
    def host(self) -> str:
        """Return normalized host."""
        return self._base_url.removeprefix("http://")

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self._base_url}/management.html",
            "Cookie": "winet_lang=en",
        }

    async def _post(self, payload: str) -> dict[str, Any]:
        url = f"{self._base_url}/ajax/get-registers"
        if payload.startswith("key=007") or payload.startswith("key=008") or payload.startswith("key=011"):
            url = f"{self._base_url}/ajax/set-registers"

        try:
            async with self._session.post(
                url,
                data=payload,
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise SirioApiConnectionError(str(err)) from err

        if not isinstance(data, dict):
            raise SirioApiError("Unexpected response payload")

        return data

    async def get_status(self) -> dict[str, Any]:
        """Read main status registers (key=001)."""
        return await self._post("key=001")

    async def get_soft_start(self) -> int:
        """Read soft-start register value."""
        data = await self._post(f"key=002&index={SOFT_START_REGISTER_INDEX}")
        value = data.get("value")
        if value is None and isinstance(data.get("content"), dict):
            value = data["content"].get("value")
        try:
            return int(value)
        except (TypeError, ValueError) as err:
            raise SirioApiError("Invalid soft-start register value") from err

    async def toggle_pump(self) -> None:
        """Toggle pump standby state."""
        await self._post("key=011")

    async def set_soft_start(self, enabled: bool) -> None:
        """Enable or disable soft start."""
        if enabled:
            await self._post(f"key=008&index={SOFT_START_REGISTER_INDEX}")
        else:
            await self._post(f"key=007&index={SOFT_START_REGISTER_INDEX}")
