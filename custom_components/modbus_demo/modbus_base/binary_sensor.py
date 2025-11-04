"""Base Modbus binary sensor."""

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import callback

from .coordinator import BaseModbusUpdateCoordinator
from .entity import BaseModbusEntity, SimpleModbusEntityDescription


@dataclass(frozen=True, kw_only=True)
class SimpleModbusBinarySensorEntityDescription(
    SimpleModbusEntityDescription, BinarySensorEntityDescription
):
    """EntityDescription of a simple Modbus binary sensor."""

    on_value: int = 1
    off_value: int = 0


class SimpleModbusBinarySensorEntity(BaseModbusEntity, BinarySensorEntity):
    """Base class for Modbus binary sensor entities."""

    entity_description: SimpleModbusBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: BaseModbusUpdateCoordinator,
        description: SimpleModbusBinarySensorEntityDescription,
    ) -> None:
        """Initialize the Modbus binary sensor."""
        super().__init__(coordinator, description)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data and (
            values := self.coordinator.data.get(self.entity_description.modbus_register)
        ):
            assert len(values) == 1, (
                "Expected exactly one register value "
                "for a SimpleModbusBinarySensorEntity"
            )
            value = values[0]

            if value == self.entity_description.on_value:
                self._attr_is_on = True
            elif value == self.entity_description.off_value:
                self._attr_is_on = False
            else:
                # Unknown values mark the entity as unavailable
                self._attr_is_on = None  # type: ignore[assignment]
                self._attr_available = False
                self.async_write_ha_state()
                return
            self._attr_available = True
        else:
            self._attr_is_on = None  # type: ignore[assignment]
            self._attr_available = False

        self.async_write_ha_state()
