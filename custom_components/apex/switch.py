import logging

from homeassistant.components.switch import SwitchEntity

from . import ApexEntity
from .const import DOMAIN, SWITCHES, FEED_CYCLES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Switch from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    
    """Loop through and add all avaliable outputs"""
    for value in entry.data["outputs"]:
        sw = Switch(entry, value, config_entry.options)
        async_add_entities([sw], False)

    """Add Feed Cycle Switches"""
    for value in FEED_CYCLES:
        _LOGGER.debug(value)
        sw = Switch(entry, value, config_entry.options)
        async_add_entities([sw], False)


class Switch(ApexEntity, SwitchEntity):
    """Define the Switch for turning ignition off/on"""

    def __init__(self, coordinator, switch, options):
        _LOGGER.debug(switch)
        self._device_id = "apex_" + switch["did"]
        self.switch = switch
        self.coordinator = coordinator
        self._state = None
        # Required for HA 2022.7
        self.coordinator_context = object()

    async def async_turn_on(self, **kwargs):
            if self.switch["type"] == "Feed":
                update = await self.coordinator.hass.async_add_executor_job(
                    self.coordinator.apex.toggle_feed_cycle,
                    self.switch["did"],
                    "ON"
                )
                if update["active"] == 1:
                    self._state = True
                    _LOGGER.debug("Writing state ON")
                    self.async_write_ha_state()
                    await self.coordinator.async_request_refresh()
            else:
                update = await self.coordinator.hass.async_add_executor_job(
                    self.coordinator.apex.toggle_output,
                    self.switch["did"],
                    "ON"
                )
                _LOGGER.debug(f"async_turn_on -> Update: {update}")
                if update["status"][0] == "ON" or update["status"][0] == "AON":
                    self._state = True
                    self.switch["status"] = update["status"]
                    _LOGGER.debug("Writing state ON")
                    self.async_write_ha_state()

           
    async def async_turn_off(self, **kwargs):
            if self.switch["type"] == "Feed":
                update = await self.coordinator.hass.async_add_executor_job(
                    self.coordinator.apex.toggle_feed_cycle,
                    self.switch["did"],
                    "OFF"
                )
                if update["active"] == 92:
                    self._state = False
                    #self.switch["status"] = update["status"]
                    _LOGGER.debug("Writing state OFF")
                    self.async_write_ha_state()
                    await self.coordinator.async_request_refresh()
            else:
                update = await self.coordinator.hass.async_add_executor_job(
                    self.coordinator.apex.toggle_output, 
                    self.switch["did"],
                    "OFF"
                )
                _LOGGER.debug(f"async_turn_off -> Update: {update}")
                if update["status"][0] == "OFF" or update["status"][0] == "AOF":
                    self._state = False
                    self.switch["status"] = update["status"]
                    _LOGGER.debug("Writing state OFF")
                    self.async_write_ha_state()

    @property
    def name(self):
        return "apex_" + self.switch["name"]

    @property
    def device_id(self):
        return self.device_id

    @property
    def is_on(self):
        if self._state == True:
            self._state = None
            return True
        elif self._state == False:
            self._state = None
            return False
        if self.switch["type"] == "Feed":
            if "feed" in self.coordinator.data and "name" in self.coordinator.data["feed"]:
                try:
                    feed_id = int(self.switch["did"])
                    return self.coordinator.data["feed"]["name"] == feed_id
                except ValueError:
                    _LOGGER.error(f"Invalid device ID format: {self.switch['did']}")
                    return False
            else:
                # _LOGGER.error("Feed data is missing from the coordinator data.")
                return False
        else:
            for value in self.coordinator.data["outputs"]:
                if value["did"] == self.switch["did"]:
                    if value["status"][0] == "ON" or value["status"][0] == "AON":
                        return True
                    else:
                        return False



    @property
    def icon(self):
        if self.switch["type"] in SWITCHES:
            return SWITCHES[self.switch["type"]]["icon"]
        else:
            _LOGGER.debug("Missing icon: " + self.switch["type"])
            return None

    @property
    def extra_state_attributes(self):
        return self.switch
