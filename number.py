from __future__ import annotations
from homeassistant.components.number import NumberDeviceClass, NumberEntity, RestoreNumber
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from . import ESPDeviceDataUpdateCoordinator
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add AccuWeather entities from a config_entry."""

    coordinator: ESPDeviceDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    numbers = []
    _numbers = coordinator.data.get("number", {})
    _LOGGER.error(f"Loading NUMBER: {_numbers}")
    for key, value in _numbers.items():
        numbers.append(Number(coordinator, key))

    async_add_entities(numbers)


class Number(CoordinatorEntity, RestoreNumber , NumberEntity):
    """Representation of a virtual numeric."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, id) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.id = id
        self._attr_unique_id = f"{coordinator.device_name}_number_{id}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_name = f"{id}"
        self._attr_native_step = 1
        self._coordinator = coordinator
        self._attr_native_value = self._get_numeric_data(coordinator.data)


    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        await self._coordinator.device.api_request("command", "POST", {"number": {f"{self.id}": int(value)}})

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._attr_native_value = self._get_numeric_data(self._coordinator.data)
        self.async_write_ha_state()

    def _get_numeric_data(self, data):
        """Get number data."""
        if "number" not in data:
            return None
        return float(data["number"].get(self.id, 0))


    async def async_added_to_hass(self) -> None:
        """Restore on startup."""
        await super().async_added_to_hass()

        if not (await self.async_get_last_number_data()):
            return
        self._attr_native_value = self.native_value
        if self.native_value != 0:
            await self.async_set_native_value(self.native_value)