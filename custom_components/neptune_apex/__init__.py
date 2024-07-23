"""The Apex Controller integration."""
import asyncio
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, NAME, DEVICEIP, MANUFACTURER, UPDATE_INTERVAL, UPDATE_INTERVAL_DEFAULT, DID, STATUS, CONFIG, TYPE
from .apex import Apex
from .apex_data_update_coordinator import ApexDataUpdateCoordinator

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

PLATFORMS = ["sensor", "switch"]

logger = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Apex component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Apex Device from a config entry."""
    user = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    deviceip = entry.data[DEVICEIP]
    if UPDATE_INTERVAL in entry.options:
        update_interval = entry.options[UPDATE_INTERVAL]
    else:
        update_interval = UPDATE_INTERVAL_DEFAULT
    logger.debug(update_interval)
    for ar in entry.data:
        logger.debug(ar)

    coordinator = ApexDataUpdateCoordinator(hass, user, password, deviceip, update_interval)

    await coordinator.async_refresh()  # Get initial data

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for component in PLATFORMS:
        await hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, component))

    async def async_set_options_service(service_call):
        await hass.async_add_executor_job(set_output, hass, service_call, coordinator)

    async def async_set_variable_service(service_call):
        await hass.async_add_executor_job(set_variable, hass, service_call, coordinator)

    async def async_set_dosing_rate_service(service_call):
        await hass.async_add_executor_job(set_dosing_rate, hass, service_call, coordinator)

    async def async_set_temperature(service_call):
        await hass.async_add_executor_job(set_temperature, hass, service_call, coordinator)

    async def async_refill_reservoir(service_call):
        await hass.async_add_executor_job(refill_reservoir, hass, service_call, coordinator)

    hass.services.async_register(DOMAIN, "set_output", async_set_options_service)
    hass.services.async_register(DOMAIN, "set_variable", async_set_variable_service)
    hass.services.async_register(DOMAIN, "set_dosing_rate", async_set_dosing_rate_service)
    hass.services.async_register(DOMAIN, "set_temperature", async_set_temperature)
    hass.services.async_register(DOMAIN, "refill_reservoir", async_refill_reservoir)

    return True


def set_output(hass, service, coordinator):
    did = service.data.get(DID).strip()
    setting = service.data.get("setting").strip()
    coordinator.apex.set_output_state(did, setting)


def set_variable(hass, service, coordinator):
    did = service.data.get(DID).strip()
    code = service.data.get("code")
    coordinator.apex.set_variable(did, code)


def set_dosing_rate(hass, service, coordinator):
    did = service.data.get(DID).strip()
    profile_id = int(service.data.get("profile_id"))
    rate = float(service.data.get("rate"))
    coordinator.apex.set_dosing_rate(did, profile_id, rate)


def set_temperature(hass, service, coordinator):
    did = service.data.get(DID).strip()
    temperature = float(service.data.get("temperature"))
    coordinator.apex.set_temperature(did, temperature)


def refill_reservoir(hass, service, coordinator):
    did = service.data.get(DID).strip()
    coordinator.apex.refill_reservoir(did)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, component) for component in PLATFORMS]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
