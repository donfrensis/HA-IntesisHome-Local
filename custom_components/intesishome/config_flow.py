"""Config flow for IntesisHome Local."""
import logging

from pyintesishome import (
    IHAuthenticationError,
    IHConnectionError,
    IntesisHomeLocal,
)
import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

class IntesisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for IntesisHome Local."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                controller = IntesisHomeLocal(
                    user_input[CONF_HOST],
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                    loop=self.hass.loop,
                    websession=async_get_clientsession(self.hass),
                )
                await controller.poll_status()
                
                if len(controller.get_devices()) == 0:
                    errors["base"] = "no_devices"
                else:
                    # Create unique_id from controller ID
                    unique_id = controller.controller_id.lower()
                    
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    # Get custom name or use default with controller ID
                    name = user_input.get(CONF_NAME)
                    if not name:
                        # Se non c'è un nome specificato, usa gli ultimi 6 caratteri del MAC
                        name = f"IntesisHome {controller.controller_id[-6:]}"

                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_HOST: user_input[CONF_HOST],
                            CONF_USERNAME: user_input[CONF_USERNAME],
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                            CONF_NAME: name
                        },
                    )

            except IHAuthenticationError:
                errors["base"] = "invalid_auth"
            except IHConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_NAME): str,
                }
            ),
            errors=errors,
        )

    async def async_step_import(self, import_data) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_data)


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""

class NoDevices(exceptions.HomeAssistantError):
    """Error to indicate the account has no devices."""