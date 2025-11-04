"""Base Modbus Entity."""

from dataclasses import dataclass

from homeassistant.helpers.entity import EntityDescription

from .const import MODBUS_REGISTERS
from .coordinator import (
    BaseModbusCoordinatorEntity,
    BaseModbusUpdateCoordinator,
    ModbusRegister,
)


@dataclass(frozen=True, kw_only=True)
class SimpleModbusEntityDescription(EntityDescription):
    """Entity description for a simple Modbus entity."""

    modbus_register: ModbusRegister


class BaseModbusEntity(BaseModbusCoordinatorEntity):
    """Base Modbus Entity."""

    def __init__(
        self,
        coordinator: BaseModbusUpdateCoordinator,
        description: SimpleModbusEntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(
            coordinator,
            context={
                MODBUS_REGISTERS: [description.modbus_register],
            },
        )
        self.entity_description = description
