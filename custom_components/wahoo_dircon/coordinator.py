from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.exceptions import HomeAssistantError

from homeassistant.components import zeroconf
import zeroconf as zc

import asyncio

from .constants import DOMAIN
from .dircon_client import prepare_data_client, run_data_client, write_data_client
from .dircon.client import DC_STATUS_CONNECTED

import logging
import datetime

_LOGGER = logging.getLogger(__name__)

RETRY_INTERVAL = 10
RETRY_COUNT = 6

ZC_TYPE = "_wahoo-fitness-tnp._tcp.local."

class Coordinator(DataUpdateCoordinator, zc.ServiceListener):

    def __init__(self, hass, entry):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update,
        )
        self._entry = entry
        self._config = entry.as_dict()["options"]
        self._title = entry.as_dict()["data"]["title"]
        self.__listeners = []
        self._client = prepare_data_client(self._config.get("host"), self._config.get("port"), self._on_dircon_data)
        self._client.add_status_listener(self._on_dircon_status)

    def add_service(self, zc, type_: str, name: str) -> None:
        _LOGGER.info(f"zc.add_service(): {type_}, {name}, {zc}")

    def remove_service(self, zc, type_: str, name: str) -> None:
        _LOGGER.info(f"zc.remove_service(): {type_}, {name}, {zc}")

    def update_service(self, zc, type_: str, name: str) -> None:
        _LOGGER.info(f"zc.update_service(): {type_}, {name}, {zc}")

    async def _async_update(self):
        return {
            "enabled": False,
            "connected": False,
        }

    def _on_dircon_data(self, data: dict):
        _LOGGER.debug(f"_on_dircon_data(): {data}")
        self._update(data)

    def _on_dircon_status(self, status: int):
        _LOGGER.debug(f"_on_dircon_status(): {status}")
        self._update({
            "connected": status == DC_STATUS_CONNECTED
        })

    async def async_load(self):
        _LOGGER.debug(f"async_load(): ")
        _zeroconf = await zeroconf.async_get_instance(self.hass)
        _zeroconf.add_service_listener(ZC_TYPE, self)

    async def async_unload(self):
        _LOGGER.debug(f"async_unload(): ")
        self.__listeners = []
        await self._client.async_close()
        _zeroconf.add_remove_listener(ZC_TYPE, self)
    
    def _add_listener(self, listener):
        self.__listeners.append(listener)

    def has_feature(self, name: str) -> bool:
        return self._config.get(name, False)

    def _update(self, data):
        self.async_set_updated_data({
            **self.data,
            **data,
        })

    async def async_toggle_enabled(self, value: bool):
        self._update({
            "enabled": value,
        })
        if value:
            await self._async_start_loop()
        else:
            await self._client.async_close()

    async def async_change_metric(self, name: str, value: float):
        _LOGGER.debug(f"async_change_metric(): change {name} to {value}")
        await write_data_client(self._client, name, value)
        self._update({
            name: value,
        })

    async def _async_start_loop(self):
        _LOGGER.debug("_async_start_loop(): (Re-)starting main loop")
        await self._client.async_close()
        self._entry.async_create_background_task(self.hass, self._async_loop(), "main_dircon_loop")

    @property
    def enabled(self) -> bool:
        return self.data.get("enabled", False)

    async def _async_loop(self):
        retry_count = 0
        while True:
            await run_data_client(self._client)
            if self.enabled:
                if retry_count >= RETRY_COUNT:
                    _LOGGER.info(f"_async_loop(): Automatically disabling due to many retries")
                    await self.async_toggle_enabled(False)
                    return
                _LOGGER.debug(f"_async_loop(): Sleeping for {RETRY_INTERVAL} secods, retries: {retry_count}")
                await asyncio.sleep(RETRY_INTERVAL)
                retry_count += 1
            if not self.enabled:
                _LOGGER.debug(f"_async_loop(): Not enabled anymore, exiting task")
                break

class BaseEntity(CoordinatorEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)
        # coordinator._add_listener(self.on_message)

    def with_name(self, name: str, id: str = None):
        self._attr_has_entity_name = True
        self._attr_unique_id = f"wahoo_dircon_{self.coordinator._entry.entry_id}_{id if id else name}"
        self._attr_name = name
        return self

    @property
    def device_info(self):
        return {
            "identifiers": {
                ("entry_id", self.coordinator._entry.entry_id), 
            },
            "name": self.coordinator._title,
        }

    def _handle_coordinator_update(self):
        self.on_data_update(self.coordinator.data)
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.on_data_update(self.coordinator.data)

    def on_data_update(self, data: dict):
        pass

class ConnectedEntity(BaseEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def available(self):
        return self.coordinator.data.get("connected", False)