from homeassistant.components import sensor
from homeassistant.const import EntityCategory

from .coordinator import ConnectedEntity
from .constants import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_setup_entities):
    coordinator = hass.data[DOMAIN]["devices"][entry.entry_id]
    entities = []
    if coordinator.has_feature("speed"):
        entities.append(_Speed(coordinator))
    if coordinator.has_feature("incline"):
        entities.append(_Incline(coordinator))
    if coordinator.has_feature("distance"):
        entities.append(_Distance(coordinator))
    if coordinator.has_feature("cadence"):
        entities.append(_Cadence(coordinator))
    if coordinator.has_feature("stride"):
        entities.append(_Stride(coordinator))
    if coordinator.has_feature("time"):
        entities.append(_Time(coordinator))
    if coordinator.has_feature("hrm"):
        entities.append(_HeartRate(coordinator))
    if coordinator.has_feature("pace"):
        entities.append(_Pace(coordinator))
    async_setup_entities(entities)

class _Distance(ConnectedEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name("Distance")
        self._attr_native_unit_of_measurement = "m"
        self._attr_suggested_unit_of_measurement = "km"
        self._attr_device_class = "distance"
        self._attr_state_class = "total_increasing"
        self._attr_suggested_display_precision = 1

    def on_data_update(self, data: dict):
        value = data.get("distance", 0)
        self._attr_native_value = value if value > 0 else None

class _Cadence(ConnectedEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name("Running cadence")
        self._attr_native_unit_of_measurement = "spm"
        self._attr_suggested_display_precision = 0
        self._attr_state_class = "measurement"
        self._attr_icon = "mdi:metronome"

    def on_data_update(self, data: dict):
        value = data.get("cadence", 0)
        self._attr_native_value = value if value > 0 else None

class _Stride(ConnectedEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name("Stride")
        self._attr_native_unit_of_measurement = "cm"
        self._attr_suggested_display_precision = 0
        self._attr_state_class = "measurement"
        self._attr_icon = "mdi:run"

    def on_data_update(self, data: dict):
        value = data.get("stride", 0)
        self._attr_native_value = value if value > 0 else None

class _Speed(ConnectedEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name("Speed", "Speed_Sensor")
        self._attr_native_unit_of_measurement = "km/h"
        self._attr_suggested_unit_of_measurement = "km/h"
        self._attr_device_class = "speed"
        self._attr_state_class = "measure"
        self._attr_suggested_display_precision = 1

    def on_data_update(self, data: dict):
        value = data.get("speed", 0)
        self._attr_native_value = value

class _Incline(ConnectedEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name("Incline", "Incline_Sensor")
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = "measure"
        self._attr_suggested_display_precision = 1
        self._attr_icon = "mdi:angle-acute"

    def on_data_update(self, data: dict):
        value = data.get("incline", 0)
        self._attr_native_value = value

class _HeartRate(ConnectedEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name("Heart Rate")
        self._attr_native_unit_of_measurement = "bpm"
        self._attr_suggested_display_precision = 0
        self._attr_state_class = "measurement"
        self._attr_icon = "mdi:heart-pulse"

    def on_data_update(self, data: dict):
        value = data.get("hrm", 0)
        self._attr_native_value = value if value > 0 else None

class _Time(ConnectedEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name("Duration")
        self._attr_native_unit_of_measurement = "s"
        self._attr_suggested_unit_of_measurement = "min"
        self._attr_device_class = "duration"
        self._attr_suggested_display_precision = 0
        self._attr_state_class = "total_increasing"

    def on_data_update(self, data: dict):
        value = data.get("time", 0)
        self._attr_native_value = value if value > 0 else None

class _Pace(ConnectedEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name("Pace")
        self._attr_native_unit_of_measurement = "s"
        self._attr_suggested_display_precision = "min"
        self._attr_suggested_display_precision = 2
        self._attr_device_class = "duration"
        self._attr_state_class = "measurement"

    def on_data_update(self, data: dict):
        value = data.get("speed", 0)
        if value == 0:
            self._attr_native_value = None
        else:
            sec_min = int(3600 / value)
            self._attr_native_value = sec_min

