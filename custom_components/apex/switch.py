import logging

from homeassistant.components.switch import SwitchEntity

from . import ApexEntity
from .const import DOMAIN, NAME, SWITCHES, STATUS, DID, TYPE, OUTPUTS

logger = logging.getLogger(__name__)

OFF = "OFF"
AUTO = "AUTO"


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Switch from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]

    for value in entry.data[STATUS][OUTPUTS]:
        sw = Switch(entry, value, config_entry.options)
        async_add_entities([sw], False)


class Switch(ApexEntity, SwitchEntity):
    """Define the Switch for turning ignition off/on"""

    def __init__(self, coordinator, switch, options):

        self._device_id = f"apex_{switch[NAME]}"
        self.switch = switch
        self.coordinator = coordinator
        self._state = None
        # Required for HA 2022.7
        self.coordinator_context = object()

    async def async_turn_on(self, **kwargs):
        update = await self.coordinator.hass.async_add_executor_job(self.coordinator.apex.set_output_state, self.switch[DID], AUTO)
        if (update is not None) and (update[STATUS][0] != OFF):
            self._state = True
            self.switch[STATUS] = update[STATUS]
            logger.debug(f"Writing state {AUTO}")
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        update = await self.coordinator.hass.async_add_executor_job(self.coordinator.apex.set_output_state, self.switch[DID], OFF)
        if (update is not None) and (update[STATUS][0] == OFF):
            self._state = False
            self.switch[STATUS] = update[STATUS]
            logger.debug(f"Writing state {OFF}")
            self.async_write_ha_state()

    @property
    def name(self):
        return "apex_" + self.switch[NAME]

    @property
    def device_id(self):
        return self.device_id

    @property
    def is_on(self):
        if self._state is True:
            self._state = None
            return True
        elif self._state is False:
            self._state = None
            return False
        for value in self.coordinator.data[STATUS][OUTPUTS]:
            if value[DID] == self.switch[DID]:
                return value[STATUS][0] != OFF

    @property
    def icon(self):
        if self.switch[TYPE] in SWITCHES:
            return SWITCHES[self.switch[TYPE]]["icon"]
        else:
            logger.debug("Missing icon: " + self.switch[TYPE])
            return None

    @property
    def extra_state_attributes(self):
        return self.switch
