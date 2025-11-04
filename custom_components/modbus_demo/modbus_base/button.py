"""Base Modbus button entity."""

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import callback

from .coordinator import BaseModbusUpdateCoordinator
from .entity import BaseModbusEntity, SimpleModbusEntityDescription


@dataclass(frozen=True, kw_only=True)
class SimpleModbusButtonEntityDescription(
    SimpleModbusEntityDescription, ButtonEntityDescription
):
    """EntityDescription of a simple Modbus button."""

    press_value: int = 1


class SimpleModbusButtonEntity(BaseModbusEntity, ButtonEntity):
    """Base class for Modbus button entities."""

    entity_description: SimpleModbusButtonEntityDescription

    def __init__(
        self,
        coordinator: BaseModbusUpdateCoordinator,
        description: SimpleModbusButtonEntityDescription,
    ) -> None:
        """Initialize the Modbus button."""
        super().__init__(coordinator, description)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # For buttons, just track availability based on having data for the register
        if self.coordinator.data and (
            self.entity_description.modbus_register in self.coordinator.data
        ):
            self._attr_available = True
        else:
            self._attr_available = False
        self.async_write_ha_state()

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.client.write_simple_struct_format(
            self.entity_description.modbus_register.address,
            self.entity_description.press_value,
            format_struct=self.entity_description.modbus_register.struct_format,
        )
