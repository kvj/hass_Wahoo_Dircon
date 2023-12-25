from homeassistant.components import binary_sensor
from homeassistant.const import EntityCategory

from .coordinator import BaseEntity
from .constants import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_setup_entities):
    coordinator = hass.data[DOMAIN]["devices"][entry.entry_id]
    async_setup_entities([_Connected(coordinator)])

class _Connected(BaseEntity, binary_sensor.BinarySensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name("Connected")
        self._attr_device_class = "connectivity"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    def on_data_update(self, data: dict):
        self._attr_is_on = data.get("connected", False) if self.coordinator.enabled else None
