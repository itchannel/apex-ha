import asyncio
import logging


from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityDescription,
    UpdateEntityFeature,
)

from homeassistant.exceptions import HomeAssistantError

from . import ApexEntity

from .const import DOMAIN

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
        """ Required for HA 2022.7 """
        self.coordinator_context = object()

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: any
    ) -> None:
        """Install an update."""
        try:
            data = await self.coordinator._hass.async_add_executor_job(self.coordinator.apex.update_firmware)
            if data == True:
                _LOGGER.debug("Update Triggered, waiting ")
                for progress in range(0, 100, 10):
                    self._attr_in_progress = progress
                    self.async_write_ha_state()
                    """ Apex official UI just has a sleep timer as the device goes completely unresponsive during update so update
                        has been set to wait 100 seconds before completing unless device comes back online first """
                    await asyncio.sleep(10)
            else:
                raise HomeAssistantError("Firmware Update Failed")
        except Exception as err:
            raise HomeAssistantError("Error while updating firmware")
        self._attr_in_progress = False
        await self.coordinator.async_refresh()

    @property
    def installed_version(self): 
        return self.coordinator.data["system"]["software"].replace("L", "")
    
    @property
    def latest_version(self):
        latest_firmware = (self.coordinator.data.get("config", {})
                           .get("nconf", {})
                           .get("latestFirmware", "Not Available"))
        return latest_firmware

    @property
    def name(self):
        return "apex_" + self.sensor