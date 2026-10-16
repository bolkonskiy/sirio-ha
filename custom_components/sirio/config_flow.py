"""Config flow for Sirio integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SirioApi, SirioApiConnectionError, SirioApiError
from .const import (
    CONF_AUTO_SOFT_START,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({CONF_HOST: str})


async def validate_host(hass: HomeAssistant, host: str) -> str:
    """Validate controller connectivity and return entry title."""
    session = async_get_clientsession(hass)
    api = SirioApi(host, session)
    await api.get_status()
    return f"Sirio ({api.host})"


class SirioConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sirio."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            await self.async_set_unique_id(host.lower())
            self._abort_if_unique_id_configured()

            try:
                title = await validate_host(self.hass, host)
            except SirioApiConnectionError:
                errors["base"] = "cannot_connect"
            except SirioApiError:
                errors["base"] = "unknown"
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=title,
                    data={CONF_HOST: SirioApi(host, async_get_clientsession(self.hass)).host},
                    options={
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                        CONF_AUTO_SOFT_START: False,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return options flow handler."""
        return SirioOptionsFlow()


class SirioOptionsFlow(OptionsFlow):
    """Handle Sirio options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage Sirio options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=2, max=300)),
                vol.Optional(
                    CONF_AUTO_SOFT_START,
                    default=options.get(CONF_AUTO_SOFT_START, False),
                ): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
