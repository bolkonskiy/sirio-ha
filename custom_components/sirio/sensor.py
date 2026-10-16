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
from homeassistant.helpers.entity import EntityCategory
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
        [
            *(
                SirioSensorEntity(coordinator, description, entry.entry_id)
                for description in SENSOR_TYPES
            ),
            SirioRuntimeSensor(coordinator, entry.entry_id, "max_current", "Максимальный ток", "ampMax", "A"),
            SirioRuntimeSensor(coordinator, entry.entry_id, "max_frequency", "Максимальная частота", "freqMax", "Hz"),
            SirioModeSensor(coordinator, entry.entry_id),
            *(
                SirioErrorCountSensor(coordinator, entry.entry_id, index, name)
                for index, name in ERROR_COUNTERS
            ),
            *(
                SirioNetworkSensor(coordinator, entry.entry_id, key, name, unit)
                for key, name, unit in NETWORK_SENSORS
            ),
        ]
    )


ERROR_COUNTERS: tuple[tuple[int, str], ...] = (
    (0, "E0 низкое напряжение"),
    (1, "E1 высокое напряжение"),
    (2, "E2 короткое замыкание"),
    (3, "E3 сухой ход"),
    (4, "E4 температура платы"),
    (5, "E5 температура IGBT"),
    (6, "E6 перегрузка"),
    (7, "E7 вне кривой"),
    (8, "E8 ошибка связи"),
    (9, "E9 предел давления"),
    (10, "E10 внешняя ошибка"),
    (11, "E11 пуски в час"),
    (12, "E12 питание 12 В"),
    (13, "E13 датчик давления"),
)

NETWORK_SENSORS: tuple[tuple[str, str, str | None], ...] = (
    ("currentIp", "IP адрес", None),
    ("currentMask", "Маска", None),
    ("currentGw", "Шлюз", None),
    ("network", "Сеть Wi-Fi", None),
    ("rssi", "RSSI", "dBm"),
    ("signal", "Сигнал", None),
    ("client", "Клиенты Wi-Fi", None),
    ("fwVer", "Прошивка", None),
    ("inetTime", "Время контроллера", None),
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


class SirioRuntimeSensor(SirioEntity, SensorEntity):
    """A runtime field that is not one of the original sensors."""

    def __init__(
        self,
        coordinator: SirioCoordinator,
        entry_id: str,
        key: str,
        name: str,
        value_key: str,
        unit: str,
    ) -> None:
        super().__init__(coordinator)
        self._value_key = value_key
        self._scale = 10 if key == "max_current" else 1
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.status.get(self._value_key)
        if raw is None:
            return None
        return float(raw) / self._scale


class SirioModeSensor(SirioEntity, SensorEntity):
    """ON, STAND-BY or ERROR, same as the panel status icon."""

    def __init__(self, coordinator: SirioCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_mode"
        self._attr_name = "Режим"
        self._attr_icon = "mdi:pump"

    @property
    def native_value(self) -> str:
        status = self.coordinator.data.status
        if int(status.get("flagError", 0)) == 1:
            return "ERROR"
        if int(status.get("standBy", 0)) == 1:
            return "STAND-BY"
        return "ON"


class SirioErrorCountSensor(SirioEntity, SensorEntity):
    """How many times one alarm code has been raised."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:counter"

    def __init__(
        self,
        coordinator: SirioCoordinator,
        entry_id: str,
        index: int,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._index = index
        self._attr_unique_id = f"{entry_id}_e{index}"
        self._attr_name = name

    @property
    def native_value(self) -> int | None:
        raw = self.coordinator.data.status.get(f"e{self._index}")
        if raw is None:
            return None
        return int(raw)


class SirioNetworkSensor(SirioEntity, SensorEntity):
    """A field from the status page."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: SirioCoordinator,
        entry_id: str,
        key: str,
        name: str,
        unit: str | None,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{entry_id}_net_{key}"
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        if key == "rssi":
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH

    @property
    def native_value(self) -> str | int | None:
        network = self.coordinator.data.network
        if not network or self._key not in network:
            return None
        value = network[self._key]
        if self._key in {"rssi", "signal", "client"}:
            return int(value)
        return str(value)
