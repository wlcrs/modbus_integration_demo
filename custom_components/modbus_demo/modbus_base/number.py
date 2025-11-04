"""Base Modbus number entity."""

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.core import callback

from .coordinator import BaseModbusUpdateCoordinator
from .entity import BaseModbusEntity, SimpleModbusEntityDescription


@dataclass(frozen=True, kw_only=True)
class SimpleModbusNumberEntityDescription(
    SimpleModbusEntityDescription, NumberEntityDescription
):
    """EntityDescription of a simple Modbus number."""

    scale: float | None = None
    """When set, the device value will be multiplied by this scale for display."""


class SimpleModbusNumberEntity(BaseModbusEntity, NumberEntity):
    """Base class for Modbus number entities."""

    entity_description: SimpleModbusNumberEntityDescription

    def __init__(
        self,
        coordinator: BaseModbusUpdateCoordinator,
        description: SimpleModbusNumberEntityDescription,
    ) -> None:
        """Initialize the Modbus number."""
        super().__init__(coordinator, description)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data and (
            values := self.coordinator.data.get(self.entity_description.modbus_register)
        ):
            assert len(values) == 1, (
                "Expected exactly one register value for a SimpleModbusNumberEntity"
            )
            value = values[0]
            if self.entity_description.scale is not None:
                assert isinstance(value, (int, float)), (
                    "Scale can only be set for registers containing a number"
                )
                value = value * self.entity_description.scale
            self._attr_native_value = value
            self._attr_available = True
        else:
            self._attr_native_value = None
            self._attr_available = False

        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        # Reverse scale for writing if needed
        to_write: Any = value
        if self.entity_description.scale not in (None, 0):
            to_write = value / self.entity_description.scale  # type: ignore[operator]

        await self.coordinator.client.write_simple_struct_format(
            self.entity_description.modbus_register.address,
            to_write,
            format_struct=self.entity_description.modbus_register.struct_format,
        )
        self.coordinator.data[self.entity_description.modbus_register] = (to_write,)
        self.coordinator.async_update_listeners()
