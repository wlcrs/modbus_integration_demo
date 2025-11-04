"""Modbus base component for Home Assistant."""

from .binary_sensor import (
    SimpleModbusBinarySensorEntity,
    SimpleModbusBinarySensorEntityDescription,
)
from .button import SimpleModbusButtonEntity, SimpleModbusButtonEntityDescription
from .coordinator import BaseModbusUpdateCoordinator
from .entity import BaseModbusEntity, ModbusRegister, SimpleModbusEntityDescription
from .number import SimpleModbusNumberEntity, SimpleModbusNumberEntityDescription
from .select import SimpleModbusSelectEntity, SimpleModbusSelectEntityDescription
from .sensor import SimpleModbusSensorEntity, SimpleModbusSensorEntityDescription
from .switch import SimpleModbusSwitchEntity, SimpleModbusSwitchEntityDescription

__all__ = [
    "BaseModbusEntity",
    "BaseModbusUpdateCoordinator",
    "ModbusRegister",
    "SimpleModbusBinarySensorEntity",
    "SimpleModbusBinarySensorEntityDescription",
    "SimpleModbusButtonEntity",
    "SimpleModbusButtonEntityDescription",
    "SimpleModbusEntityDescription",
    "SimpleModbusNumberEntity",
    "SimpleModbusNumberEntityDescription",
    "SimpleModbusSelectEntity",
    "SimpleModbusSelectEntityDescription",
    "SimpleModbusSensorEntity",
    "SimpleModbusSensorEntityDescription",
    "SimpleModbusSwitchEntity",
    "SimpleModbusSwitchEntityDescription",
]
