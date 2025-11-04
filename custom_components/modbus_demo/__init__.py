"""The Modbus Demo integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.exceptions import ConfigEntryNotReady
from tmodbus import AsyncModbusClient, create_async_tcp_client

from .const import UNIT_ID, UPDATE_INTERVAL
from .modbus_base import BaseModbusUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


@dataclass
class ModbusDemoConfigEntryData:
    """Modbus Demo config entry runtime data."""

    client: AsyncModbusClient
    coordinator: BaseModbusUpdateCoordinator


type ModbusDemoConfigEntry = ConfigEntry[ModbusDemoConfigEntryData]


async def async_setup_entry(hass: HomeAssistant, entry: ModbusDemoConfigEntry) -> bool:
    """Set up Modbus Demo from a config entry."""
    client = create_async_tcp_client(
        entry.data[CONF_HOST], port=entry.data[CONF_PORT], unit_id=UNIT_ID
    )

    try:
        await client.connect()
    except Exception as e:
        _LOGGER.exception("Error connecting to Modbus device")
        msg = "Could not connect to the Modbus device"
        raise ConfigEntryNotReady(msg) from e

    _LOGGER.debug(
        "Connected to the Modbus device at %s:%s",
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
    )
    entry.runtime_data = ModbusDemoConfigEntryData(
        client=client,
        coordinator=BaseModbusUpdateCoordinator(
            hass, _LOGGER, client, "Demo", UPDATE_INTERVAL
        ),
    )

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ModbusDemoConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, _PLATFORMS):
        await entry.runtime_data.client.disconnect()

    return unload_ok
