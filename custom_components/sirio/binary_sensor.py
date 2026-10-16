"""Binary sensor platform for Sirio."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SOFT_START_ENABLED_VALUE
from .coordinator import SirioCoordinator
from .entity import SirioEntity


@dataclass(frozen=True, kw_only=True)
class SirioBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describe a Sirio binary sensor."""

    is_on: str


BINARY_SENSOR_TYPES: tuple[SirioBinarySensorEntityDescription, ...] = (
    SirioBinarySensorEntityDescription(
        key="running",
        translation_key="running",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on="running",
    ),
    SirioBinarySensorEntityDescription(
        key="error",
        translation_key="error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on="error",
    ),
    SirioBinarySensorEntityDescription(
        key="pump_enabled",
        translation_key="pump_enabled",
        is_on="pump_enabled",
        icon="mdi:pump",
    ),
    SirioBinarySensorEntityDescription(
        key="soft_start",
        translation_key="soft_start",
        is_on="soft_start",
        icon="mdi:fan-speed-1",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sirio binary sensors."""
    coordinator: SirioCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SirioBinarySensorEntity(coordinator, description, entry.entry_id)
        for description in BINARY_SENSOR_TYPES
    )


class SirioBinarySensorEntity(SirioEntity, BinarySensorEntity):
    """Representation of a Sirio binary sensor."""

    entity_description: SirioBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: SirioCoordinator,
        description: SirioBinarySensorEntityDescription,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        status = self.coordinator.data.status
        kind = self.entity_description.is_on

        if kind == "running":
            return float(status.get("amp", 0)) / 10 > 0
        if kind == "error":
            return int(status.get("errorNumber", 0)) > 0
        if kind == "pump_enabled":
            return int(status.get("standBy", 1)) == 0
        if kind == "soft_start":
            soft_start = self.coordinator.data.soft_start
            return soft_start == SOFT_START_ENABLED_VALUE if soft_start is not None else None

        return None

    @property
    def icon(self) -> str | None:
        """Return dynamic icon for pump enabled state."""
        if self.entity_description.key == "pump_enabled":
            return "mdi:pump" if self.is_on else "mdi:pump-off"
        return self.entity_description.icon
