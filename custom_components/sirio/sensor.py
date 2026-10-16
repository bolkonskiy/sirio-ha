"""Sensor platform for Sirio."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfPower, UnitOfPressure, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SirioCoordinator
from .entity import SirioEntity


@dataclass(frozen=True, kw_only=True)
class SirioSensorEntityDescription(SensorEntityDescription):
    """Describe a Sirio sensor entity."""

    value_key: str | None = None
    template: str | None = None


def _pressure(value: dict) -> float:
    return round(float(value.get("press", 0)) / 10, 1)


def _current(value: dict) -> float:
    return round(float(value.get("amp", 0)) / 10, 2)


def _set_pressure(value: dict) -> float:
    return round(float(value.get("setPointPress", 0)) / 10, 1)


def _power(value: dict) -> float:
    return round(float(value.get("volt", 0)) * float(value.get("amp", 0)) / 10, 1)


SENSOR_TYPES: tuple[SirioSensorEntityDescription, ...] = (
    SirioSensorEntityDescription(
        key="pressure",
        translation_key="pressure",
        native_unit_of_measurement=UnitOfPressure.BAR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_key="press",
    ),
    SirioSensorEntityDescription(
        key="voltage",
        translation_key="voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_key="volt",
    ),
    SirioSensorEntityDescription(
        key="current",
        translation_key="current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_key="amp",
    ),
    SirioSensorEntityDescription(
        key="frequency",
        translation_key="frequency",
        native_unit_of_measurement="Hz",
        state_class=SensorStateClass.MEASUREMENT,
        value_key="freq",
    ),
    SirioSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_key="temp",
    ),
    SirioSensorEntityDescription(
        key="igbt_temperature",
        translation_key="igbt_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_key="tempIgbt",
    ),
    SirioSensorEntityDescription(
        key="set_pressure",
        translation_key="set_pressure",
        native_unit_of_measurement=UnitOfPressure.BAR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_key="setPointPress",
    ),
    SirioSensorEntityDescription(
        key="starts",
        translation_key="starts",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
        value_key="nrStarts",
    ),
    SirioSensorEntityDescription(
        key="hours_on",
        translation_key="hours_on",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:timer-outline",
        value_key="hPowerOn",
    ),
    SirioSensorEntityDescription(
        key="hours_running",
        translation_key="hours_running",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:engine-outline",
        value_key="hPowerRunning",
    ),
    SirioSensorEntityDescription(
        key="error_code",
        translation_key="error_code",
        icon="mdi:alert-circle-outline",
        value_key="errorNumber",
    ),
    SirioSensorEntityDescription(
        key="power",
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SirioSensorEntityDescription(
        key="standby",
        translation_key="standby",
        icon="mdi:power-standby",
        value_key="standBy",
    ),
    SirioSensorEntityDescription(
        key="soft_start_value",
        translation_key="soft_start_value",
        icon="mdi:fan-speed-1",
    ),
)

TRANSFORMS = {
    "pressure": _pressure,
    "current": _current,
    "set_pressure": _set_pressure,
    "power": _power,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sirio sensors."""
    coordinator: SirioCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SirioSensorEntity(coordinator, description, entry.entry_id)
        for description in SENSOR_TYPES
    )


class SirioSensorEntity(SirioEntity, SensorEntity):
    """Representation of a Sirio sensor."""

    entity_description: SirioSensorEntityDescription

    def __init__(
        self,
        coordinator: SirioCoordinator,
        description: SirioSensorEntityDescription,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def native_value(self) -> float | int | str | None:
        """Return sensor state."""
        if self.entity_description.key == "soft_start_value":
            return self.coordinator.data.soft_start

        status = self.coordinator.data.status
        key = self.entity_description.key

        if key in TRANSFORMS:
            return TRANSFORMS[key](status)

        value_key = self.entity_description.value_key
        if value_key is None:
            return None

        raw = status.get(value_key)
        if raw is None:
            return None

        if key in {"starts", "hours_on", "hours_running", "error_code", "standby"}:
            return int(raw)

        if key in {"frequency", "temperature", "igbt_temperature", "voltage"}:
            return float(raw)

        return raw
