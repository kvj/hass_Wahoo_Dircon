from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import selector

from .constants import DOMAIN
from .dircon_client import async_fetch_capabilities

import voluptuous as vol
import logging

_LOGGER = logging.getLogger(__name__)

async def _load_features(data: dict) -> dict | None:
    result = await async_fetch_capabilities(data.get("host", ""), data.get("port", 0))
    return result

async def _validate(hass, input: dict) -> (str | None, dict):
    features = await _load_features(input)
    if not features:
        return "connection_error", None
    return None, input

def _create_schema(hass, input: dict, flow: str = "config"):
    schema = vol.Schema({})
    if flow == "config":
        schema = schema.extend({
            vol.Required("title", default=input.get("title")): selector({"text": {}}),
        })
    
    schema = schema.extend({
        vol.Required("host", default=input.get("host")): selector({
            "text": {}
        }),
        vol.Required("port", default=input.get("port")): selector({
            "number": {
                "min": 0,
                "max": 65535,
                "step": 1,
                "mode": "box",
            }
        }),
    })
    cap_map = {}
    for cp in ["speed", "speed_set", "pace", "incline", "incline_set", "distance", "time", "cadence", "hrm", "stride"]:
        cap_map[vol.Required(cp, default=input.get(cp, False))] = selector({"boolean": {}})
    schema = schema.extend(cap_map)
    return schema

class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_zeroconf(self, zc_input=None):
        _LOGGER.debug(f"async_step_zeroconf(): {zc_input}")
        data = {
            "title": zc_input.name.split(".")[0],
            "host": str(zc_input.ip_address),
            "port": zc_input.port,
        }
        self.context["title_placeholders"] = data
        id = "{}:{}".format(data["host"], data["port"])
        await self.async_set_unique_id(id)
        return self.async_show_form(step_id="user", data_schema=_create_schema(self.hass, data))

    async def async_step_user(self, user_input=None):
        if user_input is None:
            ph = self.context.get("title_placeholders", {})
            user_input = {
                "host": ph.get("host", ""),
                "port": ph.get("port", 36866),
                "title": ph.get("title", "Wahoo Device"),
            }
            if "host" in ph and "port" in ph:
                feat = await _load_features(ph)
                user_input = {
                    **user_input,
                    **(feat if feat else {}),
                }
            _LOGGER.debug(f"async_step_user(): Show empty, placeholders: {ph}, input = {user_input}")
            return self.async_show_form(step_id="user", data_schema=_create_schema(self.hass, user_input))
        else:
            _LOGGER.debug(f"async_step_user(): Saving {user_input}")
            err, data = await _validate(self.hass, user_input)
            if err is None:
                id = "{}:{}".format(user_input["host"], user_input["port"])
                await self.async_set_unique_id(id)
                self._abort_if_unique_id_configured()
                _LOGGER.debug(f"async_step_user(): Ready to save: {data}")
                return self.async_create_entry(title=data["title"], options=data, data={"title": data["title"]})
            else:
                return self.async_show_form(step_id="user", data_schema=_create_schema(self.hass, user_input), errors=dict(base=err))

    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, entry):
        self.config_entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is None:
            _LOGGER.debug(f"Making options: {self.config_entry.as_dict()}")
            return self.async_show_form(step_id="init", data_schema=_create_schema(self.hass, self.config_entry.as_dict()["options"], flow="options"))
        else:
            _LOGGER.debug(f"Input: {user_input}")
            err, data = await _validate(self.hass, user_input)
            if err is None:
                _LOGGER.debug(f"Ready to update: {data}")
                result = self.async_create_entry(title="", data=data)
                return result
            else:
                return self.async_show_form(step_id="init", data_schema=_create_schema(self.hass, user_input), errors=dict(base=err))
