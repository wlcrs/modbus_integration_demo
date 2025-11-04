"""Base Modbus select entity."""

from dataclasses import dataclass, field

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import callback

from .coordinator import BaseModbusUpdateCoordinator
from .entity import BaseModbusEntity, SimpleModbusEntityDescription


@dataclass(frozen=True, kw_only=True)
class SimpleModbusSelectEntityDescription(
    SimpleModbusEntityDescription, SelectEntityDescription
):
    """EntityDescription of a simple Modbus select."""

    # Map between option string and Modbus register value
    options_map: dict[str, int] = field(default_factory=dict)


class SimpleModbusSelectEntity(BaseModbusEntity, SelectEntity):
    """Base class for Modbus select entities."""

    entity_description: SimpleModbusSelectEntityDescription

    def __init__(
        self,
        coordinator: BaseModbusUpdateCoordinator,
        description: SimpleModbusSelectEntityDescription,
    ) -> None:
        """Initialize the Modbus select."""
        # Ensure description.options reflects the mapping keys if not set
        if not description.options and description.options_map:
            # dataclasses with frozen=True prevent mutation;
            # rely on SelectEntity to read .options from description
            # So we set _attr_options on the entity directly in __init__
            pass
        super().__init__(coordinator, description)
        # Keep entity options consistent with mapping, fallback to description.options
        if description.options_map:
            self._attr_options = list(description.options_map.keys())

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data and (
            values := self.coordinator.data.get(self.entity_description.modbus_register)
        ):
            assert len(values) == 1, (
                "Expected exactly one register value for a SimpleModbusSelectEntity"
            )
            value = values[0]
            # Map value to option
            option = None
            for opt, reg_val in self.entity_description.options_map.items():
                if reg_val == value:
                    option = opt
                    break
            if option is None and self.entity_description.options_map:
                # Unknown value; mark unavailable
                self._attr_available = False
                self.async_write_ha_state()
                return
            self._attr_current_option = option
            self._attr_available = True
        else:
            self._attr_current_option = None
            self._attr_available = False

        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in self.options:
            msg = f"Invalid option: {option}"
            raise ValueError(msg)

        if not self.entity_description.options_map:
            msg = "No options_map provided for Modbus select"
            raise ValueError(msg)

        to_write = self.entity_description.options_map[option]

        await self.coordinator.client.write_simple_struct_format(
            self.entity_description.modbus_register.address,
            to_write,
            format_struct=self.entity_description.modbus_register.struct_format,
        )
        self.coordinator.data[self.entity_description.modbus_register] = (to_write,)
        self.coordinator.async_update_listeners()
