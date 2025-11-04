# Modbus Integration Demo

This repository contains a demo of a modbus integration using:

- the [tModbus](https://github.com/wlcrs/tmodbus) library
- Intelligent clustering of requests by the DataUpdateCoordinator of [`modbus_base`](custom_components/modbus_demo/modbus_base/coordinator.py).


Specifying Modbus entities becomes quite simple, cfr [`sensor.py`](custom_components/modbus_demo/sensor.py).

## Simple scenario: entities from 1 modbus register

In the most basic scenario (your value is computed by 1 modbus register), you can leverage the `SimpleModbusSensorEntityDescription` and specify said register in the `modbus_register` attribute:

```py
    SimpleModbusSensorEntityDescription(
        key="unix_timestamp",
        name="Unix timestamp",
        modbus_register=ModbusRegister.create_uint32_register(
            address=300, input_register=True
        ),
    ),
```

The "magic" happens in `entity.py`, where this modbus_register is passed in the context to the update coordinator:

```py
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
```

## Advanced scenario: entity from multiple modbus registers

More complex sensors, that need to query multiple registers, can do so by passing the required
modbus registers in the context themselves:

```py
class AdvancedSensorEntity(BaseModbusCoordinatorEntity):
    """Base Modbus Entity."""

    reg1 = ModbusRegister.create_uint32_register(address=1)
    reg2 = ModbusRegister.create_uint32_register(address=101)

    def __init__(
        self,
        coordinator: BaseModbusUpdateCoordinator,
        description: SimpleModbusEntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(
            coordinator,
            context={
                MODBUS_REGISTERS: [reg1, reg2],
            },
        )


    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data and (
            reg1_value := self.coordinator.data.get(reg1)
        ) and (
            reg2_value := self.coordinator.data.get(reg2)
        ):
            # the value variables are tuples, in this case only with one value
            self._attr_native_value = reg1_value[0] * reg2_value[0]
            self._attr_available = True
        else:
            self._attr_native_value = None
            self._attr_available = False

        self.async_write_ha_state()


```
