"""Base Modbus DataUpdateCoordinator."""

import logging
import struct
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import timedelta
from itertools import chain
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from tmodbus import AsyncModbusClient
from tmodbus.exceptions import TModbusError
from tmodbus.utils.word_aware_struct import WordOrderAwareStruct

from .const import MODBUS_REGISTERS

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModbusRegister:
    """Modbus register definition."""

    address: int
    """Modbus register address."""
    struct_format: struct.Struct
    """Struct format used to encode/decode the register value."""

    input_register: bool = False
    """Whether this is an input register."""

    @classmethod
    def create_uint16_register(
        cls, address: int, *, input_register: bool = False
    ) -> "ModbusRegister":
        """Create a Modbus register definition for an unsigned 16-bit integer."""
        return cls(
            address=address,
            struct_format=struct.Struct(">H"),
            input_register=input_register,
        )

    @classmethod
    def create_int16_register(
        cls, address: int, *, input_register: bool = False
    ) -> "ModbusRegister":
        """Create a Modbus register definition for a signed 16-bit integer."""
        return cls(
            address=address,
            struct_format=struct.Struct(">h"),
            input_register=input_register,
        )

    @classmethod
    def create_uint32_register(
        cls, address: int, *, input_register: bool = False
    ) -> "ModbusRegister":
        """Create a Modbus register definition for an unsigned 32-bit integer."""
        return cls(
            address=address,
            struct_format=struct.Struct(">I"),
            input_register=input_register,
        )

    @classmethod
    def create_int32_register(
        cls, address: int, *, input_register: bool = False
    ) -> "ModbusRegister":
        """Create a Modbus register definition for a signed 32-bit integer."""
        return cls(
            address=address,
            struct_format=struct.Struct(">i"),
            input_register=input_register,
        )

    @classmethod
    def create_float32_register(
        cls, address: int, *, input_register: bool = False
    ) -> "ModbusRegister":
        """Create a Modbus register definition for a 32-bit float."""
        return cls(
            address=address,
            struct_format=struct.Struct(">f"),
            input_register=input_register,
        )

    @classmethod
    def create_float64_register(
        cls, address: int, *, input_register: bool = False
    ) -> "ModbusRegister":
        """Create a Modbus register definition for a 64-bit float."""
        return cls(
            address=address,
            struct_format=struct.Struct(">d"),
            input_register=input_register,
        )


class BaseModbusUpdateCoordinator(
    DataUpdateCoordinator[dict[ModbusRegister, tuple[Any, ...]]]
):
    """A specialised DataUpdateCoordinator for Huawei Solar entities."""

    client: AsyncModbusClient

    def __init__(  # noqa: PLR0913
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        client: AsyncModbusClient,
        name: str,
        update_interval: timedelta | None = None,
        request_refresh_debouncer: Debouncer | None = None,
    ) -> None:
        """Create a HuaweiSolarUpdateCoordinator."""
        super().__init__(
            hass,
            logger,
            name=name,
            update_interval=update_interval,
            update_method=None,
            request_refresh_debouncer=request_refresh_debouncer,
        )
        self.client = client
        assert client.connected, (
            "Coordinator expects a connected Modbus client at initialization time"
        )

    async def _async_update_data(self) -> dict[ModbusRegister, tuple[Any, ...]]:
        modbus_registers = set(
            chain.from_iterable(ctx[MODBUS_REGISTERS] for ctx in self.async_contexts())
        )
        if not modbus_registers:
            _LOGGER.debug("No Modbus registers to update")

        try:
            return await batch_read_registers(self.client, modbus_registers)
        except TModbusError as err:
            msg = f"Could not update values: {err}"
            raise UpdateFailed(msg) from err


BaseModbusCoordinatorEntity = CoordinatorEntity[BaseModbusUpdateCoordinator]

MAX_BATCHED_REGISTERS_COUNT = 64
MAX_BATCHED_REGISTERS_GAP = 1


@dataclass(frozen=True)
class BatchedModbusRegisters(ModbusRegister):
    """Batched Modbus registers definition."""

    original_registers: list[ModbusRegister] = field(default_factory=list)
    """List of original Modbus registers included in this batched register."""


def batch_modbus_register(
    registers: Iterable[ModbusRegister],
    *,
    input_register: bool,
) -> list[BatchedModbusRegisters]:
    """Batch Modbus registers into minimal set of registers covering all addresses."""
    # only consider registers of the requested type
    registers = [reg for reg in registers if reg.input_register == input_register]

    if not registers:
        return []

    # sorted registers contains the de-duplicated and sorted list of registers
    sorted_registers = sorted({*registers}, key=lambda reg: reg.address)

    batched_registers: list[BatchedModbusRegisters] = []

    current_batch_start_idx = 0
    current_batch_struct_format: str = sorted_registers[0].struct_format.format.lstrip(
        ">"
    )
    current_batch_struct_size: int = sorted_registers[0].struct_format.size
    for idx, reg in enumerate(sorted_registers[1:], start=1):
        current_end_address = (
            sorted_registers[current_batch_start_idx].address
            + current_batch_struct_size
        )
        if reg.address < current_end_address:
            msg = f"Overlapping Modbus registers detected at address {reg.address}"
            raise ValueError(msg)

        if (
            reg.address > current_end_address
            or current_batch_struct_size > MAX_BATCHED_REGISTERS_COUNT * 2
        ):
            # gap or size limit detected, finalize current batched register
            batched_registers.append(
                BatchedModbusRegisters(
                    address=sorted_registers[current_batch_start_idx].address,
                    struct_format=struct.Struct(current_batch_struct_format),
                    original_registers=sorted_registers[current_batch_start_idx:idx],
                )
            )
            # start new batched register
            current_batch_start_idx = idx
            current_batch_struct_format = reg.struct_format.format.lstrip(">")
            current_batch_struct_size = reg.struct_format.size
        else:
            # extend current batched register
            current_batch_struct_format += reg.struct_format.format.lstrip(">")
            current_batch_struct_size += reg.struct_format.size

    # finalize last batched register
    if current_batch_start_idx is not None:
        assert current_batch_struct_format is not None
        batched_registers.append(
            BatchedModbusRegisters(
                address=sorted_registers[current_batch_start_idx].address,
                struct_format=struct.Struct(current_batch_struct_format),
                original_registers=sorted_registers[current_batch_start_idx:],
            )
        )

    return batched_registers


async def _batch_read_registers_of_type(
    client: AsyncModbusClient,
    batched_registers: list[BatchedModbusRegisters],
    *,
    input_register: bool,
) -> dict[ModbusRegister, tuple[Any, ...]]:
    result: dict[ModbusRegister, tuple[Any, ...]] = {}

    for batched_reg in batched_registers:
        try:
            response = await client.read_struct_format(
                batched_reg.address,
                format_struct=batched_reg.struct_format,
                input_register=input_register,
            )
        except TModbusError:
            _LOGGER.exception(
                "Read error while reading register %d with format %s",
                batched_reg.address,
                batched_reg.struct_format.format,
            )

        tuple_start_idx = 0

        for original_reg in batched_reg.original_registers:
            number_of_values = len(
                WordOrderAwareStruct.parse_format_lengths(
                    batched_reg.struct_format.format,
                )
            )
            result[original_reg] = tuple(
                response[tuple_start_idx : tuple_start_idx + number_of_values]
            )
            tuple_start_idx += number_of_values

        assert tuple_start_idx == len(response), (
            "Not all values were consumed from the response"
        )
    return result


async def batch_read_registers(
    client: AsyncModbusClient,
    registers: Iterable[ModbusRegister],
) -> dict[ModbusRegister, tuple[Any, ...]]:
    """Read multiple registers."""
    result: dict[ModbusRegister, tuple[Any, ...]] = {}

    for input_register in (False, True):
        batched_registers = batch_modbus_register(
            registers, input_register=input_register
        )
        result.update(
            await _batch_read_registers_of_type(
                client, batched_registers, input_register=input_register
            )
        )

    return result
