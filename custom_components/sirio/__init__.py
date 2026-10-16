"""The Sirio integration."""

from __future__ import annotations

from pathlib import Path
import logging

import aiohttp

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SirioApi
from .const import DOMAIN
from .coordinator import SirioCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sirio from a config entry."""
    await _async_register_manual(hass)
    session = async_get_clientsession(hass)
    api = SirioApi(entry.data[CONF_HOST], session)
    coordinator = SirioCoordinator(hass, entry, api)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_register_manual(hass: HomeAssistant) -> None:
    """Serve the dialog snippet that shows the manual text."""
    store = hass.data.setdefault(DOMAIN, {})
    if store.get("manual_js"):
        return
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                "/sirio/manual",
                str(Path(__file__).parent / "www"),
                cache_headers=False,
            )
        ]
    )
    add_extra_js_url(hass, "/sirio/manual/more-info.js?v=2")
    store["manual_js"] = True
