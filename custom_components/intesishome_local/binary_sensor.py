"""Support for IntesisHome Local connectivity sensor."""
from __future__ import annotations

import logging
import asyncio
import async_timeout
import aiohttp
from datetime import timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the IntesisHome binary sensors."""
    
    config = config_entry.data
    host = config[CONF_HOST]
    name = config[CONF_NAME]
    controller = hass.data[DOMAIN][config_entry.entry_id]["controller"]

    async def async_check_connection():
        """Check if the device is reachable."""
        try:
            async with async_timeout.timeout(2):  # Timeout ridotto a 2 secondi
                async with aiohttp.request('HEAD', f"http://{host}", raise_for_status=False) as response:
                    return response.status == 200
        except:  # Cattura qualsiasi errore
            return False

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="intesishome_local_connectivity",
        update_method=async_check_connection,
        update_interval=timedelta(seconds=30),
    )

    # Immediate first update
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        IntesisConnectivitySensor(
            coordinator,
            config_entry.entry_id,
            name,
            host,
            controller
        )
    ])

class IntesisConnectivitySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for IntesisHome device connectivity."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry_id: str,
        name: str,
        host: str,
        controller: object,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry_id = config_entry_id
        self._attr_unique_id = f"{controller.controller_id}_connectivity"
        self._attr_name = f"{name} Connectivity"
        self._host = host
        self._attr_device_info = {
            "identifiers": {(DOMAIN, controller.controller_id)},
            "name": name,
            "manufacturer": "Intesis",
            "model": getattr(controller, "model", None),
            "sw_version": getattr(controller, "version", None),
            "via_device": self._config_entry_id
        }

    @property
    def is_on(self) -> bool:
        """Return true if device is connected."""
        return self.coordinator.data