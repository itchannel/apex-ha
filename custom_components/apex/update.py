import logging
import re

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityDescription,
    UpdateEntityFeature,
)

from . import ApexEntity

from .const import DOMAIN, SENSORS, MEASUREMENTS

_LOGGER = logging.getLogger(__name__)
FIRMWARE_UPDATE_ENTITY = UpdateEntityDescription(
    key="firmware",
    translation_key="firmware",
    device_class=UpdateDeviceClass.FIRMWARE,
)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    sensor = ApexUpdate(entry, "update", config_entry.options)
    async_add_entities([sensor], True)


class ApexUpdate(
    ApexEntity,
    UpdateEntity,
):
    _attr_supported_features = (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
    )
    def __init__(self, coordinator, sensor, options):

        self.sensor = sensor
        self.options = options
        self._attr = {}
        self.coordinator = coordinator
        self._device_id = "apex_" + sensor
        # Required for HA 2022.7
        self.coordinator_context = object()

    @property
    def installed_version(self): 
        return self.coordinator.data["system"]["software"]
    
    @property
    def latest_version(self):
        return self.coordinator.data["config"]["nconf"]["latestFirmware"]
    
    @property
    def name(self):
        return "apex_" + self.sensor