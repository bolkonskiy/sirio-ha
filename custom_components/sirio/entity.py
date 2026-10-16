"""Base entity for Sirio integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import SirioCoordinator


class SirioEntity(CoordinatorEntity[SirioCoordinator]):
    """Base class for Sirio entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SirioCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
            configuration_url=f"http://{coordinator.api.host}/management.html",
        )
