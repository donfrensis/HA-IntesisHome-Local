"""The IntesisHome Local integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from pyintesishome import (
    IHAuthenticationError,
    IHConnectionError,
    IntesisHomeLocal,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "intesishome_local"
PLATFORMS = [Platform.CLIMATE, Platform.BINARY_SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IntesisHome from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create controller for this specific device
    try:
        controller = IntesisHomeLocal(
            entry.data[CONF_HOST],
            entry.data.get("username", ""),
            entry.data.get("password", ""),
            loop=hass.loop,
            websession=async_get_clientsession(hass),
        )
        
        await controller.poll_status()
        
    except (IHAuthenticationError, IHConnectionError) as ex:
        _LOGGER.error("Failed to connect to IntesisHome device: %s", str(ex))
        raise ConfigEntryNotReady from ex

    # Store the controller and config
    hass.data[DOMAIN][entry.entry_id] = {
        "controller": controller,
        "config": entry.data,
    }

    # Register device in registry
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, controller.controller_id)},
        manufacturer="Intesis",
        name=entry.data.get(CONF_NAME, f"IntesisHome {controller.controller_id[-6:]}"),
        model=getattr(controller, "model", None),
        sw_version=getattr(controller, "version", None),
        configuration_url=f"http://{entry.data[CONF_HOST]}"
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Disconnect controller and remove data
        controller = hass.data[DOMAIN][entry.entry_id]["controller"]
        await controller.stop()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok