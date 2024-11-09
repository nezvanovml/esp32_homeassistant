from __future__ import annotations
from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
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

    switches = []
    _switches = coordinator.data.get("switch", {})
    _LOGGER.error(f"Loading SWITCH: {_switches}")
    for key, value in _switches.items():
        switches.append(Switch(coordinator, key))

    async_add_entities(switches)


class Switch(CoordinatorEntity, SwitchEntity):
    """Representation of a switch."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, id) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.id = id
        self._attr_unique_id = f"{coordinator.device_name}_switch_{id}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_name = f"{id}"
        self._coordinator = coordinator
        self._attr_is_on = self._get_switch_data(coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._coordinator.device.api_request("command", "POST", {"switch": {f"{self.id}": True}})
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        await self._coordinator.device.api_request("command", "POST", {"switch": {f"{self.id}": False}})
        await self._coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._attr_is_on = self._get_switch_data(self._coordinator.data)
        self.async_write_ha_state()

    def _get_switch_data(self, data):
        """Get switch data."""
        if "switch" not in data:
            return None
        return bool(data["switch"].get(self.id, False))

