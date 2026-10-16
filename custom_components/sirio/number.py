"""Writable numeric parameters of a Sirio controller."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SirioApiError
from .const import DOMAIN
from .coordinator import SirioCoordinator
from .entity import SirioEntity
from .params import NUMBERS, NumberParam


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sirio number parameters."""
    coordinator: SirioCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SirioNumberEntity(coordinator, param, entry.entry_id) for param in NUMBERS
    )


class SirioNumberEntity(SirioEntity, NumberEntity):
    """One numeric Sirio register, shown in panel units."""

    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: SirioCoordinator,
        param: NumberParam,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._param = param
        self._attr_unique_id = f"{entry_id}_param_{param.index}"
        self._attr_suggested_object_id = f"sirio_{param.key}"
        self._attr_name = param.title
        self._attr_native_min_value = param.minimum
        self._attr_native_max_value = param.maximum
        self._attr_native_step = param.step
        self._attr_native_unit_of_measurement = param.unit
        self._attr_suggested_display_precision = param.precision
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def native_value(self) -> float | None:
        """Return the panel value."""
        raw = self.coordinator.data.params.get(self._param.index)
        if raw is None:
            return None
        return self._param.display(raw)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Manual note and the raw register."""
        raw = self.coordinator.data.params.get(self._param.index)
        return {
            "name_ru": self._param.name_ru,
            "manual": self._param.manual,
            "manual_ru": self._param.manual_ru,
            "custom_ui_more_info": "more-info-sirio-manual",
            "register": self._param.index,
            "raw": raw,
        }

    async def async_set_native_value(self, value: float) -> None:
        """Step the register to the requested panel value."""
        try:
            await self.coordinator.async_write_param(
                self._param.index,
                self._param.advanced,
                self._param.encode(value),
            )
        except SirioApiError as err:
            raise HomeAssistantError(str(err)) from err
