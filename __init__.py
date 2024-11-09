from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_ID, CONF_TOKEN, CONF_NAME, Platform
from .esp_device import ESP_Device, APIError, ConnectionError, InvalidMethod, DeviceUnavailable
from .const import DOMAIN, MANUFACTURER
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta
from typing import Any
from asyncio import timeout
import logging
from homeassistant.helpers.device_registry import DeviceInfo
import datetime as dt

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.NUMBER, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    device = ESP_Device(entry.data[CONF_ID], entry.data[CONF_TOKEN])
    coordinator = ESPDeviceDataUpdateCoordinator(hass, device, await device.unique_id, await device.token, await device.version)
    await coordinator.async_config_entry_first_refresh()
    entry.async_on_unload(entry.add_update_listener(update_listener))
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)


class ESPDeviceDataUpdateCoordinator(
    DataUpdateCoordinator[dict[str, Any]]):  # pylint: disable=hass-enforce-coordinator-module
    """Class to manage fetching data API."""

    def __init__(self, hass: HomeAssistant, device: ESP_Device, unique_id: str, token: str, version: int | None) -> None:
        """Initialize."""
        self.device = device
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer=MANUFACTURER,
            name=f"ESP32_{unique_id}",
            sw_version=version,
        )
        self.status = {}
        self.system_info = None
        self.device_name = f"ESP32_{unique_id}"
        self.time_start = None

        update_interval = timedelta(seconds=5)

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            async with timeout(10):
                if not self.system_info:
                    self.system_info = await self.device.system_info
                current = await self.device.status
        except (APIError, ConnectionError, InvalidMethod, DeviceUnavailable) as error:
            raise UpdateFailed(error) from error
        _LOGGER.error(f"Loaded data: {current}")

        # check time_start
        if current.get("time_start", None):
            time_start = dt.datetime.strptime(current.get("time_start"), "%c\n")
            _LOGGER.error(f"TIME: {time_start}")

            if not self.time_start:
                self.time_start = time_start

            if time_start > self.time_start:
                # device restarted, need restoring state
                await self.restore_controller_state()
                self.time_start = time_start

        self.status = current
        return current


    async def restore_controller_state(self):
        _LOGGER.warning((f"Restoring {await self.device.unique_id} to {self.status}"))
        if "number" in self.status:
            await self.device.api_request("command", "POST", {"number": self.status.get("number")})
