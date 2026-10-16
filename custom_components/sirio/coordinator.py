"""Data update coordinator for Sirio."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SirioApi, SirioApiConnectionError, SirioApiError
from .const import (
    CONF_AUTO_SOFT_START,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SOFT_START_POLL_INTERVAL,
    DOMAIN,
    SOFT_START_ENABLED_VALUE,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SirioData:
    """Combined controller state."""

    status: dict[str, Any]
    soft_start: int | None = None


class SirioCoordinator(DataUpdateCoordinator[SirioData]):
    """Poll Sirio controller registers."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: SirioApi,
    ) -> None:
        self.api = api
        self.entry = entry
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        self._scan_interval_seconds = scan_interval
        self._soft_start_interval = max(
            scan_interval, DEFAULT_SOFT_START_POLL_INTERVAL
        )
        self._soft_start_polls = max(
            1, self._soft_start_interval // self._scan_interval_seconds
        )
        self._poll_count = 0
        self._fail_streak = 0

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
            config_entry=entry,
        )

    async def _async_update_data(self) -> SirioData:
        try:
            status = await self.api.get_status()
        except SirioApiConnectionError as err:
            self._fail_streak += 1
            # WinET часто не успевает ответить на один опрос. Один пропуск
            # не переводит сущности в unavailable, два подряд — уже да.
            if self.data is not None and self._fail_streak < 2:
                _LOGGER.debug(
                    "Sirio poll failed, keeping last data: %s", err or type(err).__name__
                )
                return self.data
            raise UpdateFailed(
                f"Unable to connect to Sirio controller: {err or type(err).__name__}"
            ) from err
        except SirioApiError as err:
            raise UpdateFailed(str(err)) from err

        self._fail_streak = 0
        soft_start = self.data.soft_start if self.data else None
        self._poll_count += 1
        if self._poll_count >= self._soft_start_polls:
            self._poll_count = 0
            try:
                soft_start = await self.api.get_soft_start()
            except SirioApiError as err:
                _LOGGER.debug("Soft-start register read failed: %s", err)

        data = SirioData(status=status, soft_start=soft_start)

        if self.entry.options.get(CONF_AUTO_SOFT_START) and soft_start is not None:
            if soft_start != SOFT_START_ENABLED_VALUE:
                try:
                    await self.api.set_soft_start(True)
                    await asyncio.sleep(1)
                    data.soft_start = await self.api.get_soft_start()
                except SirioApiError as err:
                    _LOGGER.warning("Auto soft-start failed: %s", err)

        return data

    async def async_toggle_pump(self) -> None:
        """Toggle pump and refresh state."""
        await self.api.toggle_pump()
        await asyncio.sleep(1)
        await self.async_request_refresh()

    async def async_set_soft_start(self, enabled: bool) -> None:
        """Set soft-start and refresh state."""
        await self.api.set_soft_start(enabled)
        await asyncio.sleep(1)
        await self.async_request_refresh()
