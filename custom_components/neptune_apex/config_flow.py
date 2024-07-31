import logging
from asyncio import Task
from typing import Any, Dict, Coroutine, Mapping, Container

import voluptuous as vol
from homeassistant import config_entries, core, exceptions
from homeassistant.components.zeroconf import ZeroconfServiceInfo
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResultType
from voluptuous import Schema

from .const import SYSTEM, HOSTNAME

from .const import (
    DOMAIN,
    DEVICEIP,
    UPDATE_INTERVAL,
    UPDATE_INTERVAL_DEFAULT
)
from .apex import Apex

logger = logging.getLogger(__name__)

async def validate_input(hass: core.HomeAssistant, data):
    apex = Apex(data[CONF_USERNAME], data[CONF_PASSWORD], data[DEVICEIP])
    try:
        result = await hass.async_add_executor_job(apex.auth)
    except Exception as exc:
        logger.error(f"exception when authenticating with {data[DEVICEIP]}: {exc}")
        raise InvalidAuth from exc

    if not result:
        logger.error(f"failed to connect to {data[DEVICEIP]}")
        raise CannotConnect

    # try to get the configuration
    status = await hass.async_add_executor_job(apex.status)
    name = str(status[SYSTEM][HOSTNAME]).capitalize() if status is not None else f"Apex ({data[DEVICEIP]})"

    # return the title for the integration
    return {"title": name}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception(f"Unexpected exception {exc}")
                errors["base"] = "unknown"

        data_schema = vol.Schema({
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(DEVICEIP, default=None if user_input is None else user_input.get(DEVICEIP, None)): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo):
        # use the serial number as a unique identifier
        await self.async_set_unique_id(discovery_info.properties["sn"])
        self._abort_if_unique_id_configured()
        logger.debug(f"zeroconf discovered (device: {discovery_info.properties["sn"]}, hostname: {discovery_info.properties["hn"]}, ip_address: {discovery_info.ip_address})")
        return await self.async_step_user(user_input={DEVICEIP: discovery_info.ip_address})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        options = {
            vol.Optional(
                UPDATE_INTERVAL,
                default=self.config_entry.options.get(
                    UPDATE_INTERVAL, UPDATE_INTERVAL_DEFAULT
                ),
            ): int,
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
