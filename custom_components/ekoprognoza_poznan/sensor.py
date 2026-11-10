"""Sensors for the Ekoprognoza Poznań integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import UnitOfDensity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PAGE_URL
from .coordinator import EkoprognozaConfigEntry, EkoprognozaCoordinator
from .parser import DayForecast

STATE_ALLOWED = "allowed"
STATE_BANNED = "banned"

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EkoprognozaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            FireplaceSensor(coordinator, "kominek_dzis", 0),
            FireplaceSensor(coordinator, "kominek_jutro", 1),
            Pm10Sensor(coordinator, "pm10_dzis", 0),
            Pm10Sensor(coordinator, "pm10_jutro", 1),
            Pm10Sensor(coordinator, "pm10_pojutrze", 2),
        ]
    )


class EkoprognozaEntity(CoordinatorEntity[EkoprognozaCoordinator], SensorEntity):
    """Entity bound to the forecast card of today + days_ahead."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: EkoprognozaCoordinator, key: str, days_ahead: int
    ) -> None:
        super().__init__(coordinator)
        self._days_ahead = days_ahead
        self._attr_translation_key = key
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self.entity_id = f"sensor.{DOMAIN}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name="Ekoprognoza Poznań",
            manufacturer="Miasto Poznań",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=PAGE_URL,
        )

    @property
    def day(self) -> DayForecast | None:
        return self.coordinator.forecast_for_offset(self._days_ahead)

    @property
    def available(self) -> bool:
        # Old data stays valid after a failed refresh as long as it has a card
        # for the right date.
        return self.day is not None


class FireplaceSensor(EkoprognozaEntity):
    """Whether the anti-smog fireplace ban applies on the given day."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [STATE_ALLOWED, STATE_BANNED]
    _unrecorded_attributes = frozenset({"komunikaty", "ostrzezenia", "zrodlo"})

    @property
    def native_value(self) -> str | None:
        if (day := self.day) is None:
            return None
        return STATE_BANNED if day.fire_banned else STATE_ALLOWED

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if (day := self.day) is None:
            return None
        fetched_at = self.coordinator.fetched_at
        return {
            "data": day.date.isoformat(),
            "pm10": day.pm10,
            "poziom": day.level,
            "statusy": list(day.statuses),
            "komunikaty": list(day.messages),
            "ostrzezenia": list(day.warnings),
            "prognoza": self._days_ahead > 0,
            "zrodlo": PAGE_URL,
            "pobrano": fetched_at.isoformat() if fetched_at else None,
        }


class Pm10Sensor(EkoprognozaEntity):
    """Forecast 24h PM10 concentration for the given day."""

    _attr_device_class = SensorDeviceClass.PM10
    _attr_native_unit_of_measurement = UnitOfDensity.MICROGRAMS_PER_CUBIC_METER

    @property
    def native_value(self) -> int | None:
        if (day := self.day) is None:
            return None
        return day.pm10

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if (day := self.day) is None:
            return None
        return {"data": day.date.isoformat(), "poziom": day.level}
