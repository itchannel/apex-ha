import logging
import re

from homeassistant.helpers.entity import Entity

from .apex_entity import ApexEntity
from .const import DOMAIN, SENSORS, MEASUREMENTS, STATUS, DID, TYPE, CONFIG, INPUTS, OUTPUTS, OCONF, ICONF, STATE, ATTRIBUTES, DOS, DQD, IOTA, VARIABLE, VIRTUAL, CTYPE, ADVANCED, PROG

logger = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]

    for value in entry.data[STATUS][INPUTS]:
        sensor = ApexSensor(entry, value, config_entry.options)
        async_add_entities([sensor], True)
    for value in entry.data[STATUS][OUTPUTS]:
        if value[TYPE] in [DOS, DQD, VARIABLE, VIRTUAL, IOTA]:
            sensor = ApexSensor(entry, value, config_entry.options)
            async_add_entities([sensor], True)


class ApexSensor(ApexEntity, Entity):
    def __init__(self, coordinator, sensor, options):
        super().__init__("sensor", sensor, coordinator)
        self.sensor = sensor
        self.options = options
        self._attr = {}

    # Need to tidy this section up and avoid using so many for loops
    def get_value(self, ftype):
        if ftype == STATE:
            for value in self.coordinator.data[STATUS][INPUTS]:
                if value[DID] == self.sensor[DID]:
                    return value["value"]
            for value in self.coordinator.data[STATUS][OUTPUTS]:
                if value[DID] == self.sensor[DID]:
                    if self.sensor[TYPE] in [DOS, DQD]:
                        return value[STATUS][4]
                    if self.sensor[TYPE] == IOTA:
                        return value[STATUS][1]
                    if self.sensor[TYPE] in [VIRTUAL, VARIABLE]:
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
                    if self.sensor[TYPE] in [DOS, DQD]:
                        return value
                    if self.sensor[TYPE] == IOTA:
                        return value
                    if self.sensor[TYPE] in [VIRTUAL, VARIABLE]:
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
        test = re.findall(r"Set\s\D*(\d+)", prog)
        if test:
            # logger.debug(test[0])
            return int(test[0])
        else:
            return prog     
    
    @property
    def state(self):
        return self.get_value(STATE)

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
            logger.debug("missing icon: " + self.sensor[TYPE])
            return None
