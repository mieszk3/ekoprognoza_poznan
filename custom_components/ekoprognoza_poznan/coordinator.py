"""Data coordinator for the Ekoprognoza Poznań integration."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import date, datetime, timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later, async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    FORECAST_URL,
    LOGGER,
    REFRESH_TIMES,
    REQUEST_TIMEOUT,
    RETRY_INTERVAL,
)
from .parser import DayForecast, ParseError, forecast_for, parse

type EkoprognozaConfigEntry = ConfigEntry[EkoprognozaCoordinator]


class EkoprognozaCoordinator(DataUpdateCoordinator[list[DayForecast]]):
    """Fetches the forecast page at fixed times of day."""

    config_entry: EkoprognozaConfigEntry

    def __init__(self, hass: HomeAssistant, entry: EkoprognozaConfigEntry) -> None:
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=None,
        )
        self.fetched_at: datetime | None = None
        self._cancel_retry: Callable[[], None] | None = None

    @callback
    def async_setup_schedule(self) -> None:
        """Refresh at fixed times and re-select days after midnight."""
        entry = self.config_entry
        for hour, minute in REFRESH_TIMES:
            entry.async_on_unload(
                async_track_time_change(
                    self.hass,
                    self._async_scheduled_refresh,
                    hour=hour,
                    minute=minute,
                    second=0,
                )
            )
        entry.async_on_unload(
            async_track_time_change(
                self.hass, self._async_new_day, hour=0, minute=1, second=0
            )
        )
        entry.async_on_unload(self._async_cancel_retry)

    def forecast_for_offset(self, days_ahead: int) -> DayForecast | None:
        """Return the card for today + days_ahead, if the page has it."""
        if not self.data:
            return None
        return forecast_for(self.data, _today() + timedelta(days=days_ahead))

    async def _async_update_data(self) -> list[DayForecast]:
        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await session.get(FORECAST_URL)
                response.raise_for_status()
                html = await response.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Error fetching {FORECAST_URL}: {err}") from err

        try:
            days = await self.hass.async_add_executor_job(parse, html, _today())
        except ParseError as err:
            raise UpdateFailed(f"Unexpected page layout: {err}") from err

        self.fetched_at = dt_util.utcnow()
        return days

    async def _async_scheduled_refresh(self, _now: datetime | None = None) -> None:
        self._async_cancel_retry()
        await self.async_refresh()
        if not self.last_update_success:
            self._cancel_retry = async_call_later(
                self.hass, RETRY_INTERVAL, self._async_scheduled_refresh
            )

    @callback
    def _async_new_day(self, _now: datetime) -> None:
        self.async_update_listeners()

    @callback
    def _async_cancel_retry(self) -> None:
        if self._cancel_retry is not None:
            self._cancel_retry()
            self._cancel_retry = None


def _today() -> date:
    return dt_util.now().date()
