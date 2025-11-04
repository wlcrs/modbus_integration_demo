"""Config flow for the Modbus Demo integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow as BaseConfigFlow
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.exceptions import HomeAssistantError
from tmodbus import create_async_tcp_client
from tmodbus.exceptions import TModbusError

from .const import DOMAIN, UNIT_ID

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Adjust the schema as needed for your integration
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="45.8.248.56"): str,
        vol.Required(CONF_PORT, default=502): int,
    }
)

SERIAL_NUMBER_REGISTER = 1


async def validate_input(_hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    client = create_async_tcp_client(
        host=data[CONF_HOST], port=data[CONF_PORT], unit_id=UNIT_ID
    )

    try:
        async with client:
            serial_number = await client.read_uint16(SERIAL_NUMBER_REGISTER)
            # you can retrieve more information from the device if needed
    except TModbusError as e:
        _LOGGER.exception("Validation of connection parameters failed. Check host/port")
        raise CannotConnect from e

    # Return info that you want to store in the config entry.
    return {
        "title": "Name of the device",
        "serial_number": serial_number,
    }


class ConfigFlow(BaseConfigFlow, domain=DOMAIN):
    """Handle a config flow for Modbus Demo."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):  # noqa: N818
    """Error to indicate we cannot connect."""
