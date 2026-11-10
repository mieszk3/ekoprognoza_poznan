"""The Ekoprognoza Poznań integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import EkoprognozaConfigEntry, EkoprognozaCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: EkoprognozaConfigEntry) -> bool:
    coordinator = EkoprognozaCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    coordinator.async_setup_schedule()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EkoprognozaConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
