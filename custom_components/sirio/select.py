"""Writable choice parameters of a Sirio controller."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SirioApiError
from .const import DOMAIN
from .coordinator import SirioCoordinator
from .entity import SirioEntity
from .params import SELECTS, SelectParam

UNKNOWN = "---"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sirio select parameters."""
    coordinator: SirioCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SirioSelectEntity(coordinator, param, entry.entry_id) for param in SELECTS
    )


class SirioSelectEntity(SirioEntity, SelectEntity):
    """One Sirio register whose raw values are named choices."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SirioCoordinator,
        param: SelectParam,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._param = param
        self._attr_unique_id = f"{entry_id}_param_{param.index}"
        self._attr_suggested_object_id = f"sirio_{param.key}"
        self._attr_name = param.title

    @property
    def options(self) -> list[str]:
        """Return panel labels. Unknown raw values stay visible as ---."""
        labels = list(self._param.options.values())
        raw = self.coordinator.data.params.get(self._param.index)
        if raw is not None and raw not in self._param.options:
            return [*labels, UNKNOWN]
        return labels

    @property
    def current_option(self) -> str | None:
        """Return the current panel label."""
        raw = self.coordinator.data.params.get(self._param.index)
        if raw is None:
            return None
        return self._param.options.get(raw, UNKNOWN)

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

    async def async_select_option(self, option: str) -> None:
        """Step the register to the selected label."""
        if option == UNKNOWN:
            return
        raw = next(
            (value for value, label in self._param.options.items() if label == option),
            None,
        )
        if raw is None:
            raise HomeAssistantError(f"Неизвестный вариант {option}")
        try:
            await self.coordinator.async_write_param(
                self._param.index,
                self._param.advanced,
                raw,
            )
        except SirioApiError as err:
            raise HomeAssistantError(str(err)) from err
