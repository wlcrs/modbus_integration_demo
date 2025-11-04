"""Base Modbus Sensor."""

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import callback

from .coordinator import BaseModbusUpdateCoordinator
from .entity import BaseModbusEntity, SimpleModbusEntityDescription


@dataclass(frozen=True, kw_only=True)
class SimpleModbusSensorEntityDescription(
    SimpleModbusEntityDescription, SensorEntityDescription
):
    """EntityDescription of a Simple Modbus sensor."""

    scale: float | None = None
    """When set, the value returned by the device will be multiplied by this scale."""


class SimpleModbusSensorEntity(BaseModbusEntity, SensorEntity):
    """Base class for Modbus sensor entities."""

    entity_description: SimpleModbusSensorEntityDescription

    def __init__(
        self,
        coordinator: BaseModbusUpdateCoordinator,
        description: SimpleModbusSensorEntityDescription,
    ) -> None:
        """Initialize the Modbus sensor."""
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
