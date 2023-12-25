from homeassistant.components import switch
from homeassistant.const import EntityCategory

from .coordinator import BaseEntity
from .constants import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_setup_entities):
    coordinator = hass.data[DOMAIN]["devices"][entry.entry_id]
    async_setup_entities([_Enabled(coordinator)])

class _Enabled(BaseEntity, switch.SwitchEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name("Connect")
        self._attr_device_class = "switch"
        self._attr_icon = "mdi:power"

    def on_data_update(self, data: dict):
        self._attr_is_on = self.coordinator.enabled

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_toggle_enabled(True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_toggle_enabled(False)
