from __future__ import annotations
from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from . import esp_device
from .const import DOMAIN
from . import ESPDeviceDataUpdateCoordinator
import logging
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from datetime import timedelta
import async_timeout
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add AccuWeather entities from a config_entry."""

    coordinator: ESPDeviceDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    binary_sensors = []
    _sensors = coordinator.data.get("binary_sensor", {})
    _LOGGER.error(f"Loading BS: {_sensors}")
    for key, value in _sensors.items():
        binary_sensors.append(SimpleBinarySensor(coordinator, key))
    async_add_entities(binary_sensors)

class SimpleBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a binary sensor."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, id) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.id = id
        self._attr_unique_id = f"{coordinator.device_name}_binary_sensor_{id}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_name = f"{id}"
        self._coordinator = coordinator
        self._attr_is_on = self._get_sensor_data(coordinator.data)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._attr_is_on = self._get_sensor_data(self._coordinator.data)
        self.async_write_ha_state()

    def _get_sensor_data(self, data):
        """Get sensor data."""
        if "binary_sensor" not in data:
            return None
        return bool(data["binary_sensor"].get(self.id, None))
