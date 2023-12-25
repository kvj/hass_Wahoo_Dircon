from homeassistant.components import number
from homeassistant.const import EntityCategory

from .coordinator import ConnectedEntity
from .constants import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_setup_entities):
    coordinator = hass.data[DOMAIN]["devices"][entry.entry_id]
    entities = []
    if coordinator.has_feature("speed") and coordinator.has_feature("speed_set"):
        entities.append(_Speed(coordinator))
    if coordinator.has_feature("incline") and coordinator.has_feature("incline_set"):
        entities.append(_Incline(coordinator))
    async_setup_entities(entities)

class _Speed(ConnectedEntity, number.NumberEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name("Speed")
        self._attr_native_step = 0.1
        self._attr_native_unit_of_measurement = "km/h"
        self._attr_device_class = "speed"
        self._attr_mode = "box"

    def on_data_update(self, data: dict):
        self._attr_native_value = data.get("speed", 0)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_change_metric("speed", value)

class _Incline(ConnectedEntity, number.NumberEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name("Incline")
        self._attr_native_step = 0.5
        self._attr_native_min_value = -40
        self._attr_native_max_value = 40
        self._attr_native_unit_of_measurement = "%"
        self._attr_mode = "box"
        self._attr_icon = "mdi:angle-acute"

    def on_data_update(self, data: dict):
        self._attr_native_value = data.get("incline", 0)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_change_metric("incline", value)
