"""Data update coordinator for Sirio."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
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
    DOMAIN,
    SOFT_START_DISABLED_VALUE,
    SOFT_START_ENABLED_VALUE,
    SOFT_START_REGISTER_INDEX,
)
from .params import PARAM_INDEXES, PARAMS_BY_INDEX

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SirioData:
    """Combined controller state."""

    status: dict[str, Any]
    params: dict[int, int] = field(default_factory=dict)
    network: dict[str, Any] | None = None
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
        self._cursor = 0
        self._scans = 0
        self._fail_streak = 0
        self._catalog_done = False

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
        if self.data is None:
            data = SirioData(status=status)
        else:
            self.data.status = status
            data = self.data

        # Полный каталог читается фоновой задачей и не держит старт HA.
        # Пока он идет, опрос только обновляет runtime.
        if self._catalog_done:
            params = data.params
            index = PARAM_INDEXES[self._cursor % len(PARAM_INDEXES)]
            self._cursor += 1
            spec = PARAMS_BY_INDEX[index]
            value = await self._read_one(index, spec.advanced)
            if value is not None:
                params[index] = value
            self._scans += 1
            if self._scans % 6 == 0:
                network = await self._read_network()
                if network is not None:
                    data.network = network

        data.soft_start = data.params.get(SOFT_START_REGISTER_INDEX)

        if (
            self.entry.options.get(CONF_AUTO_SOFT_START)
            and data.soft_start == SOFT_START_DISABLED_VALUE
        ):
            try:
                value = await self.api.set_soft_start(True)
                data.soft_start = value
                data.params[SOFT_START_REGISTER_INDEX] = value
            except SirioApiError as err:
                _LOGGER.warning("Auto soft-start failed: %s", err)

        return data

    async def async_load_catalog(self) -> None:
        """Read every parameter after setup, without blocking startup."""
        started = time.monotonic()
        try:
            network = await self._read_network()
            if self.data is not None and network is not None:
                self.data.network = network
                self.async_set_updated_data(self.data)
            loaded = 0
            for index in PARAM_INDEXES:
                spec = PARAMS_BY_INDEX[index]
                value = await self._read_one(index, spec.advanced)
                if self.data is None:
                    return
                if value is not None:
                    self.data.params[index] = value
                    loaded += 1
                    if index == SOFT_START_REGISTER_INDEX:
                        self.data.soft_start = value
                self.async_set_updated_data(self.data)
            _LOGGER.info(
                "Sirio catalog loaded in %.0f s, %s registers",
                time.monotonic() - started,
                loaded,
            )
        finally:
            self._catalog_done = True

    async def _read_one(self, index: int, advanced: bool) -> int | None:
        try:
            return await self.api.read_param(index, advanced)
        except SirioApiError as err:
            _LOGGER.debug("Parameter %s read failed: %s", index, err)
            return None

    async def _read_network(self) -> dict[str, Any] | None:
        try:
            return await self.api.get_network()
        except SirioApiError as err:
            _LOGGER.debug("Network status read failed: %s", err)
            return None

    async def async_toggle_pump(self) -> None:
        """Toggle pump and refresh state."""
        await self.api.toggle_pump()
        await self.async_request_refresh()

    async def async_set_soft_start(self, enabled: bool) -> None:
        """Set soft-start and refresh the cached register."""
        await self.async_write_param(
            SOFT_START_REGISTER_INDEX,
            False,
            SOFT_START_ENABLED_VALUE if enabled else SOFT_START_DISABLED_VALUE,
        )

    async def async_write_param(self, index: int, advanced: bool, target: int) -> None:
        """Write one register and keep the new raw value in the cache."""
        value = await self.api.write_raw(index, advanced, target)
        if self.data is None:
            await self.async_request_refresh()
            return
        self.data.params[index] = value
        if index == SOFT_START_REGISTER_INDEX:
            self.data.soft_start = value
        self.async_set_updated_data(self.data)
