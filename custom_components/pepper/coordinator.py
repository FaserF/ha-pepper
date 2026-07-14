import asyncio
import logging
import random
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .pepper_api import PepperAPI

_LOGGER = logging.getLogger(__name__)


class PepperDataUpdateCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Class to manage fetching Pepper data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: PepperAPI,
        sort_mode: str,
        update_interval_min: int,
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self.sort_mode = sort_mode

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_interval_min),
        )

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch data from Pepper API."""
        # Add a random jitter delay to evade anti-bot profiling
        jitter = random.uniform(1.0, 5.0)
        _LOGGER.debug("Waiting for random jitter delay of %.2fs", jitter)
        await asyncio.sleep(jitter)

        try:
            # Run the synchronous API call in an executor thread
            return await self.hass.async_add_executor_job(
                self.api.get_deals,
                self.sort_mode,
            )
        except Exception as err:
            raise UpdateFailed(f"Error fetching Pepper deals: {err}") from err
