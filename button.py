from __future__ import annotations
from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
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

    buttons = []
    _buttons = coordinator.data.get("button", [])
    _LOGGER.error(f"Loading BUTTON: {_buttons}")
    for key in _buttons:
        buttons.append(Button(coordinator, key))
    async_add_entities(buttons)


class Button(CoordinatorEntity, ButtonEntity):
    """Representation of a button."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, id) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.id = id
        self._attr_unique_id = f"{coordinator.device_name}_button_{id}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_name = f"{id}"
        self._coordinator = coordinator

    async def async_press(self, **kwargs: Any) -> None:
        """Press button."""
        await self._coordinator.device.api_request("command", "POST", {"button": [self.id]})
        # await self._coordinator.async_request_refresh()

