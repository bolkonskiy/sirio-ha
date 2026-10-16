"""Switch platform for Sirio."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SOFT_START_ENABLED_VALUE
from .coordinator import SirioCoordinator
from .entity import SirioEntity


@dataclass(frozen=True, kw_only=True)
class SirioSwitchEntityDescription(SwitchEntityDescription):
    """Describe a Sirio switch."""


SWITCH_TYPES: tuple[SirioSwitchEntityDescription, ...] = (
    SirioSwitchEntityDescription(
        key="pump",
        translation_key="pump",
        icon="mdi:pump",
    ),
    SirioSwitchEntityDescription(
        key="soft_start",
        translation_key="soft_start",
        icon="mdi:fan-speed-1",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sirio switches."""
    coordinator: SirioCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SirioSwitchEntity(coordinator, description, entry.entry_id)
        for description in SWITCH_TYPES
    )


class SirioSwitchEntity(SirioEntity, SwitchEntity):
    """Representation of a Sirio switch."""

    entity_description: SirioSwitchEntityDescription

    def __init__(
        self,
        coordinator: SirioCoordinator,
        description: SirioSwitchEntityDescription,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        status = self.coordinator.data.status
        if self.entity_description.key == "pump":
            return int(status.get("standBy", 1)) == 0
        soft_start = self.coordinator.data.soft_start
        if soft_start is None:
            return None
        return soft_start == SOFT_START_ENABLED_VALUE

    @property
    def icon(self) -> str | None:
        """Return dynamic icon."""
        if self.entity_description.key == "pump":
            return "mdi:pump" if self.is_on else "mdi:pump-off"
        return self.entity_description.icon

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        if self.entity_description.key == "pump":
            if not self.is_on:
                await self.coordinator.async_toggle_pump()
            return
        if self.is_on is not True:
            await self.coordinator.async_set_soft_start(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        if self.entity_description.key == "pump":
            if self.is_on:
                await self.coordinator.async_toggle_pump()
            return
        if self.is_on is not False:
            await self.coordinator.async_set_soft_start(False)
