import logging
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, MANUFACTURER, DID, STATUS, TYPE, SYSTEM
from .coordinator import ApexDataUpdateCoordinator

logger = logging.getLogger(__name__)


class ApexEntity(CoordinatorEntity):
    def __init__(self, entity_type: str, entity: dict, coordinator: ApexDataUpdateCoordinator):
        super().__init__(coordinator)

        # we do not pass a name up the tree
        self._device_id = self._attr_unique_id = f"{coordinator.hostname}_{entity[NAME]}".lower().replace("-", "_")
        self._attr_name = f"{coordinator.hostname.capitalize()} {entity[NAME]}"
        logger.debug(f"{entity_type}.{self._device_id} = (NAME: {entity[NAME]}, DID: {entity[DID]}, TYPE: {entity[TYPE]})")

        # just a HASS requirement
        self.coordinator_context = object()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    @property
    def device_id(self):
        return self._device_id

    @property
    def device_info(self):
        if self._device_id is None:
            return None

        return {
            "identifiers": {(DOMAIN, self.coordinator.deviceip)},
            NAME: self.coordinator.hostname.capitalize(),
            "hw_version": self.coordinator.data[STATUS][SYSTEM]["hardware"],
            "sw_version": self.coordinator.data[STATUS][SYSTEM]["software"],
            "manufacturer": MANUFACTURER
        }
