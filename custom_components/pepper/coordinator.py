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


class PepperDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Pepper data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: PepperAPI,
        sort_mode: str,
        update_interval_min: int,
        limit: int,
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self.sort_mode = sort_mode
        self.limit = limit

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_interval_min),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Pepper API."""
        # Add a random jitter delay to evade anti-bot profiling
        jitter = random.uniform(1.0, 5.0)
        _LOGGER.debug("Waiting for random jitter delay of %.2fs", jitter)
        await asyncio.sleep(jitter)

        def _fetch_all_data() -> dict[str, Any]:
            # Fetch normal deals
            deals = self.api.get_deals(self.sort_mode, limit=self.limit)
            # Fetch freebies (force higher limit of 100 to ensure client-side filter finds freebies)
            freebies = self.api.get_deals(
                self.sort_mode, is_freebies=True, limit=max(100, self.limit)
            )
            # Fetch vouchers
            vouchers = self.api.get_deals(
                self.sort_mode, is_voucher=True, limit=self.limit
            )
            # Fetch user profile if logged in
            profile = None
            if self.api.username:
                profile = self.api.get_user_profile()
            return {
                "deals": deals,
                "freebies": freebies,
                "vouchers": vouchers,
                "profile": profile,
            }

        try:
            # Run the synchronous API calls in an executor thread
            return await self.hass.async_add_executor_job(_fetch_all_data)
        except Exception as err:
            raise UpdateFailed(f"Error fetching Pepper data: {err}") from err
