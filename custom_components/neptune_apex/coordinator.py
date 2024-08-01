import logging
from datetime import timedelta

import async_timeout
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, STATUS, CONFIG, SYSTEM, HOSTNAME
from .apex import Apex

logger = logging.getLogger(__name__)


class ApexDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, user: str, password: str, deviceip: str, update_interval: float):
        self._hass = hass
        self.deviceip: str = deviceip
        self.apex: Apex = Apex(user, password, deviceip)
        self._available: bool = True

        super().__init__(
            hass,
            logger,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self):
        try:
            async with async_timeout.timeout(30):
                data = {
                    STATUS: await self._hass.async_add_executor_job(self.apex.status),
                    CONFIG: await self._hass.async_add_executor_job(self.apex.config)
                }
                logger.debug("refreshing now")
                # logger.debug(data)
                return data
        except Exception as ex:
            self._available = False  # Mark as unavailable
            logger.warning(str(ex))
            logger.warning("error communicating with Apex for %s", self.deviceip)
            raise UpdateFailed(f"error communicating with Apex for {self.deviceip}") from ex

    @property
    def hostname(self) -> str:
        return self.data[STATUS][SYSTEM][HOSTNAME]
