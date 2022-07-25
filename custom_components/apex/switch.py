import logging
import time

from homeassistant.components.switch import SwitchEntity

from . import ApexEntity
from .const import DOMAIN, SWITCHES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Switch from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    _LOGGER.debug(entry.data)
    
    #data = await hass.async_add_executor_job(
    #        entry.apex.status  # Fetch new status
    #    )
    #_LOGGER.debug(data)
    # switches = [Switch(entry)]
    # async_add_entities(switches, False)
    for value in entry.data["outputs"]:
        _LOGGER.debug(value)
        sw = Switch(entry, value, config_entry.options)
        async_add_entities([sw], False)
       # sw = Switch(entry, key, config_entry.options)
        # Only add guard entity if supported b
       # async_add_entities([sw], False)


class Switch(ApexEntity, SwitchEntity):
    """Define the Switch for turning ignition off/on"""

    def __init__(self, coordinator, switch, options):

        self._device_id = "apex_output_" + switch["did"]
        self.switch = switch
        self.coordinator = coordinator
        if self.switch["status"][0] == "ON" or self.switch["status"][0] == "AUTO":
            self._state = True
        else:
            self._state = False
        # Required for HA 2022.7
        self.coordinator_context = object()

    async def async_turn_on(self, **kwargs):
            update = await self.coordinator.hass.async_add_executor_job(
                self.coordinator.apex.toggle_output,
                self.switch["did"],
                "ON"
            )
            if update == True:
                self._state = False
                self.async_write_ha_state()

           
    async def async_turn_off(self, **kwargs):
            update = await self.coordinator.hass.async_add_executor_job(
                self.coordinator.apex.toggle_output, 
                self.switch["did"],
                "OFF"
            )
            if update == True:
                self._state = False
                self.async_write_ha_state()



    @property
    def name(self):
        return self.switch["name"]

    @property
    def device_id(self):
        return self._device_id

    @property
    def is_on(self):
        return self._state


    @property
    def icon(self):
        if self.switch["type"] in SWITCHES:
            return SWITCHES[self.switch["type"]]["icon"]
        else:
            _LOGGER.debug("Missing icon: " + self.sensor["type"])
            return None

    @property
    def extra_state_attributes(self):
        return self.switch
