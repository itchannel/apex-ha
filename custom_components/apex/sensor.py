import logging
import re

from homeassistant.helpers.entity import Entity

from . import ApexEntity
from .const import DOMAIN, SENSORS, MEASUREMENTS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]

    for value in entry.data["inputs"]:
        sensor = ApexSensor(entry, value, config_entry.options)
        async_add_entities([sensor], True)
    for value in entry.data["outputs"]:
        if value["type"] == "dos" or value["type"] == "variable" or value["type"] == "virtual" or value["type"] == "iotaPump|Sicce|Syncra":
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
        self._device_id = "apex_" + sensor["name"]
        # Required for HA 2022.7
        self.coordinator_context = object()

    # Need to tidy this section up and avoid using so many for loops
    def get_value(self, ftype):
        if ftype == "state":
            for value in self.coordinator.data["inputs"]:
                if value["did"] == self.sensor["did"]:
                    return value["value"]
            for value in self.coordinator.data["outputs"]:
                if value["did"] == self.sensor["did"]:
                    if self.sensor["type"] == "dos":
                        return value["status"][4]
                    if self.sensor["type"] == "iotaPump|Sicce|Syncra":
                        return value["status"][1]
                    if self.sensor["type"] == "virtual" or self.sensor["type"] == "variable":
                        if "config" in self.coordinator.data:
                            for config in self.coordinator.data["config"]["oconf"]:
                                if config["did"] == self.sensor["did"]:
                                    if config["ctype"] == "Advanced":
                                        return self.process_prog(config["prog"])
                                    else:
                                        return "Not an Advanced variable!"
                    
        if ftype == "attributes":
            for value in self.coordinator.data["inputs"]:
                if value["did"] == self.sensor["did"]:
                    return value
            for value in self.coordinator.data["outputs"]:
                if value["did"] == self.sensor["did"]:
                    if self.sensor["type"] == "dos":
                        return value
                    if self.sensor["type"] == "iotaPump|Sicce|Syncra":
                        return value
                    if self.sensor["type"] == "virtual" or self.sensor["type"] == "variable":
                        if "config" in self.coordinator.data:
                            for config in self.coordinator.data["config"]["oconf"]:
                                if config["did"] == self.sensor["did"]: 
                                    return config
                        else:
                            return value
    
    def process_prog(self, prog):
        if "Set PF" in prog:
            return prog
        test = re.findall("Set\s[^\d]*(\d+)", prog)
        if test:
            _LOGGER.debug(test[0])
            return int(test[0])
        else:
            return prog     
    
    @property
    def name(self):
        return "apex_" + self.sensor["name"]

    @property
    def state(self):
        return self.get_value("state")

    @property
    def device_id(self):
        return self.device_id

    @property
    def extra_state_attributes(self):
        return self.get_value("attributes")

    @property
    def unit_of_measurement(self):
        if "iconf" in self.coordinator.data["config"]:
            for value in self.coordinator.data["config"]["iconf"]:
                if value["did"] == self.sensor["did"]:
                    if "range" in value["extra"]:
                        if value["extra"]["range"] in MEASUREMENTS:
                            return MEASUREMENTS[value["extra"]["range"]]
        if self.sensor["type"] in SENSORS:
            if "measurement" in SENSORS[self.sensor["type"]]:
                return SENSORS[self.sensor["type"]]["measurement"]
        return None

    @property
    def icon(self):
        if self.sensor["type"] in SENSORS:
            return SENSORS[self.sensor["type"]]["icon"]
        else:
            _LOGGER.debug("Missing icon: " + self.sensor["type"])
            return None
