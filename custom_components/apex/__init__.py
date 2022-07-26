"""The Apex Controller integration."""
import asyncio
import logging
from datetime import timedelta

import async_timeout
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    DEVICEIP,
    MANUFACTURER,
)
from .apex import Apex

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

PLATFORMS = ["sensor", "switch"]

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Apex component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Apex Device from a config entry."""
    user = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    deviceip = entry.data[DEVICEIP]
    for ar in entry.data:
        _LOGGER.debug(ar)

    coordinator = ApexDataUpdateCoordinator(hass, user, password, deviceip)

    await coordinator.async_refresh()  # Get initial data


    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )



    return True





async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class ApexDataUpdateCoordinator(DataUpdateCoordinator):
    """DataUpdateCoordinator to handle fetching new data about the Apex Controller."""

    def __init__(self, hass, user, password, deviceip):
        """Initialize the coordinator and set up the Controller object."""
        self._hass = hass
        self.deviceip = deviceip
        self.apex = Apex(user, password, deviceip)
        self._available = True

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from Apex Controller."""
        try:
            async with async_timeout.timeout(30):
                data = await self._hass.async_add_executor_job(
                    self.apex.status  # Fetch new status
                )
                #_LOGGER.debug("Refreshing Now")
                #_LOGGER.debug(data)

                return data
        except Exception as ex:
            self._available = False  # Mark as unavailable
            _LOGGER.warning(str(ex))
            _LOGGER.warning("Error communicating with Apex for %s", self.deviceip)
            raise UpdateFailed(
                f"Error communicating with Apex for {self.deviceip}"
            ) from ex


class ApexEntity(CoordinatorEntity):
    """Defines a base Apex entity."""

    def __init__(
        self, *, device_id: str, name: str, coordinator: ApexDataUpdateCoordinator
    ):
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._name = name


    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    @property
    def name(self):
        """Return the name of the entity."""
        _LOGGER.debug(self._name)
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
            "name": f"Apex Controller ({self.coordinator.deviceip})",
            "hw_version": self.coordinator.data["system"]["hardware"],
            "sw_version": self.coordinator.data["system"]["software"],
            "manufacturer": MANUFACTURER,
            "test": "TEST"
        }


