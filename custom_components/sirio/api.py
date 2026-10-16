"""WinET REST API client for Sirio pump controllers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import ADVANCED_PIN, SOFT_START_DISABLED_VALUE, SOFT_START_ENABLED_VALUE, SOFT_START_REGISTER_INDEX

_LOGGER = logging.getLogger(__name__)

RELAY_REGISTER_INDEX = 48
RELAY_VALID_RAW = (1, 2)


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
        self._advanced_open = False
        self._lock = asyncio.Lock()

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

    async def _post(self, payload: str, path: str | None = None) -> dict[str, Any]:
        if path is not None:
            url = f"{self._base_url}{path}"
        elif payload.startswith(("key=007", "key=008", "key=009", "key=010", "key=011")):
            url = f"{self._base_url}/ajax/set-registers"
        else:
            url = f"{self._base_url}/ajax/get-registers"

        async with self._lock:
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
            finally:
                # httpd на WinET роняет соединение, если запросы идут пачкой.
                await asyncio.sleep(0.3)

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

    async def set_soft_start(self, enabled: bool) -> int:
        """Enable or disable soft start by stepping to the target raw value."""
        target = SOFT_START_ENABLED_VALUE if enabled else SOFT_START_DISABLED_VALUE
        return await self.write_raw(SOFT_START_REGISTER_INDEX, False, target)

    async def ensure_advanced(self) -> None:
        """Open advanced parameters. One successful login is enough for this session."""
        if self._advanced_open:
            return
        try:
            data = await self._post(f"pin={ADVANCED_PIN}", "/ajax/login")
        except SirioApiError as err:
            _LOGGER.debug("Advanced login failed, reading registers anyway: %s", err)
            self._advanced_open = True
            return
        if not data.get("logged"):
            _LOGGER.debug("Advanced login was not confirmed, reading registers anyway")
        self._advanced_open = True

    async def read_param(self, index: int, advanced: bool) -> int:
        """Read one base (key 002) or advanced (key 003) register."""
        if advanced:
            await self.ensure_advanced()
        key = "003" if advanced else "002"
        last_error: SirioApiError | None = None
        for _attempt in range(2):
            try:
                data = await self._post(f"key={key}&index={index}")
                return int(data["value"])
            except (SirioApiConnectionError, KeyError, TypeError, ValueError) as err:
                last_error = err if isinstance(err, SirioApiError) else SirioApiError(f"Invalid parameter {index}")
        raise last_error or SirioApiError(f"Invalid parameter {index}")

    async def step_param(self, index: int, advanced: bool, up: bool) -> int:
        """Step one register. 007/009 up, 008/010 down. The reply is the new raw value."""
        if advanced:
            await self.ensure_advanced()
            key = "009" if up else "010"
        else:
            key = "007" if up else "008"
        data = await self._post(f"key={key}&index={index}")
        try:
            return int(data["value"])
        except (KeyError, TypeError, ValueError) as err:
            raise SirioApiError(f"Parameter {index} did not step") from err

    async def write_raw(self, index: int, advanced: bool, target: int, limit: int = 280) -> int:
        """Step until the register equals target. On failure or cancel, step back."""
        if index == RELAY_REGISTER_INDEX and target not in RELAY_VALID_RAW:
            raise SirioApiError("Реле I/O принимает только N.O. или N.C.")
        start = await self.read_param(index, advanced)
        if index == RELAY_REGISTER_INDEX and start not in RELAY_VALID_RAW:
            raise SirioApiError(
                "Реле I/O сейчас не N.O. и не N.C. Шагать регистр нельзя: до нужного значения сотни шагов."
            )
        if start == target:
            return start
        current = start
        try:
            steps = 0
            while current != target and steps < limit:
                new = await self.step_param(index, advanced, target > current)
                steps += 1
                if new == current:
                    break
                current = new
            if current != target:
                raise SirioApiError(f"Параметр {index} остановился на {current}, нужно {target}")
            return current
        except BaseException:
            await self._restore(index, advanced, current, start)
            raise

    async def _restore(self, index: int, advanced: bool, current: int, start: int) -> None:
        """Put a register back. Keep going if the caller is already cancelled."""
        if current == start:
            return
        restoring = asyncio.create_task(self._walk(index, advanced, start, current))
        task = asyncio.current_task()
        while not restoring.done():
            if task is not None and hasattr(task, "uncancel"):
                task.uncancel()
            try:
                await asyncio.shield(restoring)
            except asyncio.CancelledError:
                continue
        error = restoring.exception()
        if error is not None:
            _LOGGER.error("Не удалось вернуть параметр %s к %s: %s", index, start, error)

    async def _walk(self, index: int, advanced: bool, target: int, current: int, limit: int = 280) -> int:
        steps = 0
        while current != target and steps < limit:
            new = await self.step_param(index, advanced, target > current)
            steps += 1
            if new == current:
                break
            current = new
        return current

    async def get_network(self) -> dict[str, Any]:
        """Read the status page: address, signal, firmware."""
        return await self._post("", "/ajax/get-status")
