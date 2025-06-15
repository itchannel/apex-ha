import logging
import re

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)

from . import ApexEntity
from .const import DOMAIN, SENSORS, MEASUREMENTS, MANUAL_SENSORS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):

    # _LOGGER.debug("Current configuration: %s", hass.config.as_dict())

    """Get System Temperature Unit"""
    global _SYSTEM_TEMP_UNIT
    _SYSTEM_TEMP_UNIT = hass.config.units.temperature_unit
    _LOGGER.debug("System temperature unit: %s", _SYSTEM_TEMP_UNIT)

    """Add the Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]

    for value in entry.data["inputs"]:
        sensor = ApexSensor(entry, value, config_entry.options)
        async_add_entities([sensor], True)
    for value in entry.data["outputs"]:
        if value["type"] in ("dos", "variable", "virtual", "vortech", "iotaPump|Sicce|Syncra"):
            sensor = ApexSensor(entry, value, config_entry.options)
            async_add_entities([sensor], True)
            

    """Add Feed Status Remaining Time"""
    for value in MANUAL_SENSORS:
        sensor = ApexSensor(entry, value, config_entry.options)
        async_add_entities([sensor], True)


class ApexSensor(ApexEntity, SensorEntity):
    def __init__(self, coordinator, sensor, options):
        _LOGGER.debug(sensor)
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
            if self.sensor["type"] == "feed":
                # _LOGGER.debug(f"get_value[state:feed]: coordinator.data|{self.coordinator.data}")

                if "feed" in self.coordinator.data:
                    # Determine if new or old Apex
                    apex_type = "new"

                    if "apex_type" in self.coordinator.data["feed"]:
                        apex_type = self.coordinator.data["feed"]["apex_type"]

                    # Apex Classic does feed with 6 as OFF and 1-4 as ON
                    if apex_type == 'old':

                        _LOGGER.debug(f"get_value[state:feed]: old_data|{self.coordinator.data["feed"]}")

                        name = self.coordinator.data["feed"]["name"]
                        if name == 6:
                            return 0        # feed is off
                        else:
                            feed_value = self.coordinator.data["feed"]["active"]
                            hour = feed_value
                            show_hour = 0
                            if ( feed_value > 3600 ):
                                show_hour = 1
                                hour = feed_value / 60
                            total_minutes = hour / 60
                            min = int(total_minutes)
                            sec = (total_minutes - min) * 60
                            if show_hour == 1:
                                time = f"{hour:.0f}{min:.0f}:{sec:.0f}"
                            else:
                                time = f"{min:.0f}:{sec:.0f}"
                            return time

                # Handle "feed" if not Apex Classic
                if "feed" in self.coordinator.data and "active" in self.coordinator.data["feed"]:
                    if self.coordinator.data["feed"]["active"] > 50000:
                        return 0
                    else:
                        return round(self.coordinator.data["feed"]["active"] / 60, 1)
                else:
                    return 0
            for value in self.coordinator.data["inputs"]:
                if value["did"] == self.sensor["did"]:
                    return value["value"]
            for value in self.coordinator.data["outputs"]:
                if value["did"] == self.sensor["did"]:
                    if self.sensor["type"] == "dos":
                        return value["status"][4]
                    if self.sensor["type"] == "iotaPump|Sicce|Syncra":
                        return value["status"][1]
                    if self.sensor["type"] == "vortech":
                        return f"{value["status"][0]} {value["status"][1]} {value["status"][2]}"
                    if self.sensor["type"] == "virtual" or self.sensor["type"] == "variable":
                        if "config" in self.coordinator.data:
                            config_data = self.coordinator.data["config"]
                            if "oconf" in config_data:
                                for config in self.coordinator.data["config"]["oconf"]:
                                    if config["did"] == self.sensor["did"]:
                                        if config["ctype"] == "Advanced":
                                            return self.process_prog(config["prog"])
                                        else:
                                            return "Not an Advanced variable!"
                            else:
                                if self.sensor["type"] == "variable":
                                    # _LOGGER.debug(f"get_value[state:variable]: {self.sensor|value}")
                                    if "intensity" in value:
                                        return value["intensity"]
                    
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
                            config_data = self.coordinator.data["config"]
                            if "oconf" in config_data:
                                for config in self.coordinator.data["config"]["oconf"]:
                                    if config["did"] == self.sensor["did"]:
                                        return config
                            else:
                                return value
                        else:
                            return value
    
    def process_prog(self, prog):
        if len(prog) > 255:
            return None
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
                if self.sensor["type"] == "Temp":
                    return _SYSTEM_TEMP_UNIT
                else:
                    return SENSORS[self.sensor["type"]]["measurement"]
        return None

    @property
    def state_class(self):
        if self.sensor["type"] in SENSORS:
            return SensorStateClass.MEASUREMENT
        return None

    @property
    def icon(self):
        if self.sensor["type"] in SENSORS:
            return SENSORS[self.sensor["type"]]["icon"]
        else:
            _LOGGER.debug("Missing icon: " + self.sensor["type"])
            return None
