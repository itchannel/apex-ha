import logging
from homeassistant.helpers.update_coordinator import  CoordinatorEntity

from .const import DOMAIN, NAME, MANUFACTURER, DID, STATUS, TYPE
from .apex_data_update_coordinator import ApexDataUpdateCoordinator

logger = logging.getLogger(__name__)


class ApexEntity(CoordinatorEntity):
    def __init__(self, entity_type: str, entity: dict, coordinator: ApexDataUpdateCoordinator):
        super().__init__(coordinator)
        name = self._name = entity[NAME]
        logger.debug(f"{entity_type} (NAME: {name}, DID: {entity[DID]}, TYPE: {entity[TYPE]})")

        # prefix is the coordinator.deviceip (ideally the host name)
        prefix = coordinator.deviceip.replace(".", "_")
        if prefix.endswith(".local"):
            prefix = prefix[:-6]

        self._device_id = f"{prefix}_{name}"

        # just a HASS requirement
        self.coordinator_context = object()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    @property
    def name(self):
        """Return the name of the entity."""
        logger.debug(self._name)
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the entity."""
        return f"{self.coordinator.deviceip}-{self._device_id}"

    @property
    def device_info(self):
        """Return device information about this device."""
        if self._device_id is None:
            return None

        return {
            "identifiers": {(DOMAIN, self.coordinator.deviceip)},
            NAME: f"Apex Controller ({self.coordinator.deviceip})",
            "hw_version": self.coordinator.data[STATUS]["system"]["hardware"],
            "sw_version": self.coordinator.data[STATUS]["system"]["software"],
            "manufacturer": MANUFACTURER
        }
