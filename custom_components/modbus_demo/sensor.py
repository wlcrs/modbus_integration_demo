"""Demo Modbus sensors."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .modbus_base import (
    BaseModbusUpdateCoordinator,
    ModbusRegister,
    SimpleModbusSensorEntity,
    SimpleModbusSensorEntityDescription,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from . import ModbusDemoConfigEntry

_LOGGER = logging.getLogger(__name__)

SENSORS: list[SimpleModbusSensorEntityDescription] = [
    SimpleModbusSensorEntityDescription(
        key="minute_of_hour",
        name="Minute of hour",
        modbus_register=ModbusRegister.create_uint16_register(
            address=5, input_register=True
        ),
    ),
    SimpleModbusSensorEntityDescription(
        key="unix_timestamp",
        name="Unix timestamp",
        modbus_register=ModbusRegister.create_uint32_register(
            address=300, input_register=True
        ),
    ),
]


class ModbusDemoSensorEntity(SimpleModbusSensorEntity):
    """Demo Modbus sensor entity."""

    def __init__(
        self,
        coordinator: BaseModbusUpdateCoordinator,
        description: SimpleModbusSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description)
        # Unique ID should contain with unique information from device
        # for example: prefix with serial number
        self.unique_id = f"modbus_demo_sensor_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for the sensor."""
        return DeviceInfo(
            identifiers={(DOMAIN, "demo_device")},
            name="Modbus Demo Device",
            manufacturer="Modbus Demo Inc.",
            model="Demo Model 1",
        )


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ModbusDemoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Demo sensors from config entry."""
    _LOGGER.debug(
        "Set up sensor for entry_id %s",
        config_entry.entry_id,
    )

    async_add_entities(
        [
            ModbusDemoSensorEntity(config_entry.runtime_data.coordinator, sensor)
            for sensor in SENSORS
        ],
        update_before_add=True,
    )
