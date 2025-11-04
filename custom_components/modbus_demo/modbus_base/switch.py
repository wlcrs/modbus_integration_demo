"""Base Modbus Sensor."""

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import callback

from .coordinator import BaseModbusUpdateCoordinator
from .entity import BaseModbusEntity, SimpleModbusEntityDescription


@dataclass(frozen=True, kw_only=True)
class SimpleModbusSwitchEntityDescription(
    SimpleModbusEntityDescription, SwitchEntityDescription
):
    """EntityDescription of a Simple Modbus Switch."""

    on_value: int = 1
    off_value: int = 0


class SimpleModbusSwitchEntity(BaseModbusEntity, SwitchEntity):
    """Base class for Modbus switch entities."""

    entity_description: SimpleModbusSwitchEntityDescription

    def __init__(
        self,
        coordinator: BaseModbusUpdateCoordinator,
        description: SimpleModbusSwitchEntityDescription,
    ) -> None:
        """Initialize the Modbus switch."""
        super().__init__(coordinator, description)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data and (
            values := self.coordinator.data.get(self.entity_description.modbus_register)
        ):
            assert len(values) == 1, (
                "Expected exactly one register value for a SimpleModbusSensorEntity"
            )
            value = values[0]

            if value == self.entity_description.on_value:
                self._attr_is_on = True
            elif value == self.entity_description.off_value:
                self._attr_is_on = False
            else:
                msg = (
                    f"Received unexpected value {value} for switch: "
                    f"only {self.entity_description.on_value} and "
                    f"{self.entity_description.off_value} are supported"
                )
                raise ValueError(msg)
            self._attr_available = True
        else:
            self._attr_available = False

        self.async_write_ha_state()

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Turn on the device."""
        await self.coordinator.client.write_simple_struct_format(
            self.entity_description.modbus_register.address,
            self.entity_description.on_value,
            format_struct=self.entity_description.modbus_register.struct_format,
        )
        self.coordinator.data[self.entity_description.modbus_register] = (
            self.entity_description.on_value,
        )
        self.coordinator.async_update_listeners()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn off the device."""
        await self.coordinator.client.write_simple_struct_format(
            self.entity_description.modbus_register.address,
            self.entity_description.off_value,
            format_struct=self.entity_description.modbus_register.struct_format,
        )
        self.coordinator.data[self.entity_description.modbus_register] = (
            self.entity_description.off_value,
        )
        self.coordinator.async_update_listeners()
