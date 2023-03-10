import logging
import re

from homeassistant.helpers.entity import Entity

from . import ApexEntity
from .const import DOMAIN, NAME, SENSORS, MEASUREMENTS, STATUS, DID, TYPE, CONFIG, INPUTS, OUTPUTS, OCONF, ICONF, STATE, ATTRIBUTES, DOS, IOTA, VARIABLE, VIRTUAL, CTYPE, ADVANCED, PROG

logger = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]

    for value in entry.data[STATUS][INPUTS]:
        sensor = ApexSensor(entry, value, config_entry.options)
        async_add_entities([sensor], True)
    for value in entry.data[STATUS][OUTPUTS]:
        if (value[TYPE] == DOS) or (value[TYPE] == VARIABLE) or (value[TYPE] == VIRTUAL) or (value[TYPE] == IOTA):
            sensor = ApexSensor(entry, value, config_entry.options)
            async_add_entities([sensor], True)


class ApexSensor(
    ApexEntity,
    Entity,
):
    def __init__(self, coordinator, sensor, options):

        self.sensor = sensor
        self.options = options
        self._attr = {}
        self.coordinator = coordinator
        self._device_id = f"apex_{sensor[NAME]}"
        # Required for HA 2022.7
        self.coordinator_context = object()

    # Need to tidy this section up and avoid using so many for loops
    def get_value(self, ftype):
        if ftype == STATE:
            for value in self.coordinator.data[STATUS][INPUTS]:
                if value[DID] == self.sensor[DID]:
                    return value["value"]
            for value in self.coordinator.data[STATUS][OUTPUTS]:
                if value[DID] == self.sensor[DID]:
                    if self.sensor[TYPE] == DOS:
                        return value[STATUS][4]
                    if self.sensor[TYPE] == IOTA:
                        return value[STATUS][1]
                    if (self.sensor[TYPE] == VIRTUAL) or (self.sensor[TYPE] == VARIABLE):
                        if self.coordinator.data[CONFIG] is not None:
                            for config in self.coordinator.data[CONFIG][OCONF]:
                                if config[DID] == self.sensor[DID]:
                                    if config[CTYPE] == ADVANCED:
                                        return ApexSensor.process_prog(config[PROG])
                                    else:
                                        return "Not an Advanced variable!"
                    
        if ftype == ATTRIBUTES:
            for value in self.coordinator.data[STATUS][INPUTS]:
                if value[DID] == self.sensor[DID]:
                    return value
            for value in self.coordinator.data[STATUS][OUTPUTS]:
                if value[DID] == self.sensor[DID]:
                    if self.sensor[TYPE] == DOS:
                        return value
                    if self.sensor[TYPE] == IOTA:
                        return value
                    if self.sensor[TYPE] == VIRTUAL or self.sensor[TYPE] == VARIABLE:
                        if self.coordinator.data[CONFIG] is not None:
                            for config in self.coordinator.data[CONFIG][OCONF]:
                                if config[DID] == self.sensor[DID]:
                                    return config
                        else:
                            return value
    
    @staticmethod
    def process_prog(prog):
        if "Set PF" in prog:
            return prog
        test = re.findall("Set\s[^\d]*(\d+)", prog)
        if test:
            # logger.debug(test[0])
            return int(test[0])
        else:
            return prog     
    
    @property
    def name(self):
        return "apex_" + self.sensor[NAME]

    @property
    def state(self):
        return self.get_value(STATE)

    @property
    def device_id(self):
        return self.device_id

    @property
    def extra_state_attributes(self):
        return self.get_value(ATTRIBUTES)

    @property
    def unit_of_measurement(self):
        if ICONF in self.coordinator.data[CONFIG]:
            for value in self.coordinator.data[CONFIG][ICONF]:
                if value[DID] == self.sensor[DID]:
                    if "range" in value["extra"]:
                        if value["extra"]["range"] in MEASUREMENTS:
                            return MEASUREMENTS[value["extra"]["range"]]
        if self.sensor[TYPE] in SENSORS:
            if "measurement" in SENSORS[self.sensor[TYPE]]:
                return SENSORS[self.sensor[TYPE]]["measurement"]
        return None

    @property
    def icon(self):
        if self.sensor[TYPE] in SENSORS:
            return SENSORS[self.sensor[TYPE]]["icon"]
        else:
            logger.debug("Missing icon: " + self.sensor[TYPE])
            return None
