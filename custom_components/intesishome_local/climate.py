"""Support for IntesisHome Local Smart AC Controllers."""
from __future__ import annotations

import logging
import asyncio
from random import randrange
from typing import NamedTuple

from pyintesishome import (
    IHAuthenticationError,
    IHConnectionError,
    IntesisBase,
    IntesisHomeLocal,
)
from pyintesishome.const import DEVICE_INTESISHOME_LOCAL

from homeassistant import config_entries, core
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    PRESET_BOOST,
    PRESET_COMFORT,
    PRESET_ECO,
    SWING_BOTH,
    SWING_HORIZONTAL,
    SWING_OFF,
    SWING_VERTICAL,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    UnitOfTemperature,
)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

class SwingSettings(NamedTuple):
    """Settings for swing mode."""
    vvane: str
    hvane: str

MAP_IH_TO_HVAC_MODE = {
    "auto": HVACMode.HEAT_COOL,
    "cool": HVACMode.COOL,
    "dry": HVACMode.DRY,
    "fan": HVACMode.FAN_ONLY,
    "heat": HVACMode.HEAT,
    "off": HVACMode.OFF,
}
MAP_HVAC_MODE_TO_IH = {v: k for k, v in MAP_IH_TO_HVAC_MODE.items()}

MAP_IH_TO_PRESET_MODE = {
    "eco": PRESET_ECO,
    "comfort": PRESET_COMFORT,
    "powerful": PRESET_BOOST,
}
MAP_PRESET_MODE_TO_IH = {v: k for k, v in MAP_IH_TO_PRESET_MODE.items()}

IH_SWING_STOP = "auto/stop"
IH_SWING_SWING = "swing"
MAP_SWING_TO_IH = {
    SWING_OFF: SwingSettings(vvane=IH_SWING_STOP, hvane=IH_SWING_STOP),
    SWING_BOTH: SwingSettings(vvane=IH_SWING_SWING, hvane=IH_SWING_SWING),
    SWING_HORIZONTAL: SwingSettings(vvane=IH_SWING_STOP, hvane=IH_SWING_SWING),
    SWING_VERTICAL: SwingSettings(vvane=IH_SWING_SWING, hvane=IH_SWING_STOP),
}

MAP_STATE_ICONS = {
    HVACMode.COOL: "mdi:snowflake",
    HVACMode.DRY: "mdi:water-off",
    HVACMode.FAN_ONLY: "mdi:fan",
    HVACMode.HEAT: "mdi:white-balance-sunny",
    HVACMode.HEAT_COOL: "mdi:cached",
}

MAX_RETRIES = 10
MAX_WAIT_TIME = 300

async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create climate entities from config flow."""
    controller = hass.data[DOMAIN][config_entry.entry_id]["controller"]
    config = hass.data[DOMAIN][config_entry.entry_id]["config"]

    if ih_devices := controller.get_devices():
        async_add_entities(
            [
                IntesisAC(
                    config_entry.entry_id,
                    ih_device_id, 
                    device, 
                    controller,
                    config.get(CONF_NAME)
                )
                for ih_device_id, device in ih_devices.items()
            ],
            update_before_add=True,
        )
class IntesisAC(ClimateEntity):
    """Represents an Intesishome air conditioning device."""

    def __init__(
        self, 
        config_entry_id: str,
        ih_device_id: str, 
        ih_device: dict, 
        controller: IntesisBase,
        device_name: str | None = None
    ) -> None:
        """Initialize the thermostat."""
        self._config_entry_id = config_entry_id
        self._controller = controller
        self._device_id = ih_device_id
        self._ih_device = ih_device
        
        # Use custom name if provided, otherwise use device ID
        self._attr_name = device_name or f"IntesisHome {ih_device_id[-6:]}"
        
        # Set unique_id using the device's MAC address
        self._attr_unique_id = ih_device_id
        
        # Device info for device registry - modificato per usare lo stesso ID del dispositivo
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._config_entry_id)},
        }

        self._connected = False
        self._setpoint_step = 1.0
        self._current_temp = None
        self._max_temp = None
        self._attr_hvac_modes = []
        self._min_temp = None
        self._target_temp = None
        self._outdoor_temp = None
        self._hvac_mode = None
        self._preset = None
        self._preset_list = [PRESET_ECO, PRESET_COMFORT, PRESET_BOOST]
        self._run_hours = None
        self._rssi = None
        self._swing_list = [SWING_OFF]
        self._vvane = None
        self._hvane = None
        self._power = False
        self._fan_speed = None
        self._power_consumption_heat = None
        self._power_consumption_cool = None
        
        # Inizializzazione delle feature supportate
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_supported_features |= ClimateEntityFeature.TURN_ON
        self._attr_supported_features |= ClimateEntityFeature.TURN_OFF

        # Setup swing list
        if controller.has_vertical_swing(ih_device_id):
            self._swing_list.append(SWING_VERTICAL)
        if controller.has_horizontal_swing(ih_device_id):
            self._swing_list.append(SWING_HORIZONTAL)
        if SWING_HORIZONTAL in self._swing_list and SWING_VERTICAL in self._swing_list:
            self._swing_list.append(SWING_BOTH)
        if len(self._swing_list) > 1:
            self._attr_supported_features |= ClimateEntityFeature.SWING_MODE

        # Setup fan speeds
        self._fan_modes = controller.get_fan_speed_list(ih_device_id)
        if self._fan_modes:
            self._attr_supported_features |= ClimateEntityFeature.FAN_MODE

        # Preset support
        if ih_device.get("climate_working_mode"):
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE

        # Setup HVAC modes
        if modes := controller.get_mode_list(ih_device_id):
            mode_list = []
            for mode in modes:
                if mode in MAP_IH_TO_HVAC_MODE:
                    mode_list.append(MAP_IH_TO_HVAC_MODE[mode])
                else:
                    _LOGGER.warning("Unexpected mode: %s", mode)
            self._attr_hvac_modes.extend(mode_list)
        self._attr_hvac_modes.append(HVACMode.OFF)

    async def async_added_to_hass(self):
        """Subscribe to event updates."""
        _LOGGER.debug("Added climate device with state: %s", repr(self._ih_device))
        self._controller.add_update_callback(self.async_update_callback)

        try:
            await self._controller.connect()
        except IHConnectionError as ex:
            _LOGGER.error("Exception connecting to IntesisHome: %s", ex)
            raise PlatformNotReady from ex

    @property
    def name(self):
        """Return the name of the AC device."""
        return self._attr_name

    @property
    def temperature_unit(self):
        """Intesishome API uses celsius on the backend."""
        return UnitOfTemperature.CELSIUS

    @property
    def extra_state_attributes(self):
        """Return the device specific state attributes."""
        attrs = {}
        if self._outdoor_temp is not None:
            attrs["outdoor_temp"] = self._outdoor_temp
        if self._power_consumption_heat:
            attrs["power_consumption_heat_kw"] = round(
                self._power_consumption_heat / 1000, 1
            )
        if self._power_consumption_cool:
            attrs["power_consumption_cool_kw"] = round(
                self._power_consumption_cool / 1000, 1
            )

        return attrs

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return self._device_id

    @property
    def target_temperature_step(self) -> float:
        """Return whether setpoint should be whole or half degree precision."""
        return self._setpoint_step

    @property
    def preset_modes(self):
        """Return a list of HVAC preset modes."""
        return self._preset_list

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        return self._preset

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if hvac_mode := kwargs.get(ATTR_HVAC_MODE):
            await self.async_set_hvac_mode(hvac_mode)

        if temperature := kwargs.get(ATTR_TEMPERATURE):
            _LOGGER.debug("Setting %s to %s degrees", self._device_id, temperature)
            await self._controller.set_temperature(self._device_id, temperature)
            self._target_temp = temperature

        # Write updated temperature to HA state to avoid flapping (API confirmation is slow)
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set operation mode."""
        _LOGGER.debug("Setting %s to %s mode", self._device_id, hvac_mode)
        if hvac_mode == HVACMode.OFF:
            self._power = False
            await self._controller.set_power_off(self._device_id)
            # Write changes to HA, API can be slow to push changes
            self.async_write_ha_state()
            return

        # First check device is turned on
        if not self._controller.is_on(self._device_id):
            self._power = True
            await self._controller.set_power_on(self._device_id)

        # Set the mode
        await self._controller.set_mode(self._device_id, MAP_HVAC_MODE_TO_IH[hvac_mode])

        # Send the temperature again in case changing modes has changed it
        if self._target_temp:
            await self._controller.set_temperature(self._device_id, self._target_temp)

        # Updates can take longer than 2 seconds, so update locally
        self._hvac_mode = hvac_mode
        self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode):
        """Set fan mode (from quiet, low, medium, high, auto)."""
        await self._controller.set_fan_speed(self._device_id, fan_mode)

        # Updates can take longer than 2 seconds, so update locally
        self._fan_speed = fan_mode
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode):
        """Set preset mode."""
        ih_preset_mode = MAP_PRESET_MODE_TO_IH.get(preset_mode)
        await self._controller.set_preset_mode(self._device_id, ih_preset_mode)

    async def async_set_swing_mode(self, swing_mode):
        """Set the vertical vane."""
        if swing_settings := MAP_SWING_TO_IH.get(swing_mode):
            await self._controller.set_vertical_vane(
                self._device_id, swing_settings.vvane
            )
            await self._controller.set_horizontal_vane(
                self._device_id, swing_settings.hvane
            )

    async def async_update(self):
        """Copy values from controller dictionary to climate device."""
        # Update values from controller's device dictionary
        self._connected = self._controller.is_connected
        self._current_temp = self._controller.get_temperature(self._device_id)
        self._fan_speed = self._controller.get_fan_speed(self._device_id)
        self._power = self._controller.is_on(self._device_id)
        self._min_temp = self._controller.get_min_setpoint(self._device_id)
        self._max_temp = self._controller.get_max_setpoint(self._device_id)
        self._target_temp = self._controller.get_setpoint(self._device_id)
        self._outdoor_temp = self._controller.get_outdoor_temperature(self._device_id)

        # Operation mode
        mode = self._controller.get_mode(self._device_id)
        self._hvac_mode = MAP_IH_TO_HVAC_MODE.get(mode)

        # Preset mode
        preset = self._controller.get_preset_mode(self._device_id)
        self._preset = MAP_IH_TO_PRESET_MODE.get(preset)

        # Swing mode
        self._vvane = self._controller.get_vertical_swing(self._device_id)
        self._hvane = self._controller.get_horizontal_swing(self._device_id)

        # Power consumption
        self._power_consumption_heat = self._controller.get_heat_power_consumption(
            self._device_id
        )
        self._power_consumption_cool = self._controller.get_cool_power_consumption(
            self._device_id
        )

    async def async_will_remove_from_hass(self):
        """Shutdown the controller when the device is being removed."""
        self._controller.remove_update_callback(self.async_update_callback)
        await self._controller.stop()
        self._controller = None

    @property
    def icon(self):
        """Return the icon for the current state."""
        icon = None
        if self._power:
            icon = MAP_STATE_ICONS.get(self._hvac_mode)
        return icon

    async def async_update_callback(self, device_id=None):
        """Let HA know there has been an update from the controller."""
        # Track changes in connection state
        if self._controller and not self._controller.is_connected and self._connected:
            # Connection has dropped
            self._connected = False
            reconnect_seconds = 30

            _LOGGER.info(
                "Connection to IntesisHome Local API was lost. Reconnecting in %i seconds",
                reconnect_seconds,
            )

            async def try_connect(retries):
                try:
                    await self._controller.connect()
                    _LOGGER.info("Reconnected to IntesisHome Local API")
                except IHConnectionError:
                    if retries < MAX_RETRIES:
                        wait_time = min(2**retries, MAX_WAIT_TIME)
                        _LOGGER.info(
                            "Failed to reconnect to IntesisHome Local API. Retrying in %i seconds",
                            wait_time,
                        )
                        async_call_later(self.hass, wait_time, try_connect(retries + 1))
                    else:
                        _LOGGER.error(
                            "Failed to reconnect to IntesisHome Local API after %i retries. Giving up",
                            MAX_RETRIES,
                        )

            async_call_later(self.hass, reconnect_seconds, try_connect(0))

        if self._controller.is_connected and not self._connected:
            # Connection has been restored
            self._connected = True
            _LOGGER.debug("Connection to IntesisHome Local API was restored")

        if not device_id or self._device_id == device_id:
            # Update all devices if no device_id was specified
            self.async_schedule_update_ha_state(True)

    @property
    def min_temp(self):
        """Return the minimum temperature for the current mode of operation."""
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature for the current mode of operation."""
        return self._max_temp

    @property
    def should_poll(self):
        """Poll for updates if pyIntesisHome doesn't have a socket open."""
        return True

    @property
    def fan_mode(self):
        """Return whether the fan is on."""
        return self._fan_speed

    @property
    def swing_mode(self):
        """Return current swing mode."""
        if self._vvane == IH_SWING_SWING and self._hvane == IH_SWING_SWING:
            swing = SWING_BOTH
        elif self._vvane == IH_SWING_SWING:
            swing = SWING_VERTICAL
        elif self._hvane == IH_SWING_SWING:
            swing = SWING_HORIZONTAL
        else:
            swing = SWING_OFF
        return swing

    @property
    def fan_modes(self):
        """List of available fan modes."""
        return self._fan_modes

    @property
    def swing_modes(self):
        """List of available swing positions."""
        return self._swing_list

    @property
    def available(self) -> bool:
        """If the device hasn't been able to connect, mark as unavailable."""
        return self._connected or self._connected is None

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._current_temp

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current mode of operation if unit is on."""
        if self._power:
            return self._hvac_mode
        return HVACMode.OFF

    @property
    def target_temperature(self) -> float | None:
        """Return the current setpoint temperature if unit is on."""
        if self._power and self.hvac_mode not in [HVACMode.FAN_ONLY, HVACMode.OFF]:
            return self._target_temp
        return None