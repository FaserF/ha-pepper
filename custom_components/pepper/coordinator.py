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
            # Fetch a single large batch of deals to cover all types and extract freebies/vouchers
            batch_limit = max(100, self.limit)
            all_deals = self.api.get_deals(self.sort_mode, limit=batch_limit)

            # Slice to configured limit for standard deals
            deals = all_deals[: self.limit]

            # Filter freebies client-side
            freebies = [
                d
                for d in all_deals
                if d.get("price") == 0
                or d.get("price") == 0.0
                or d.get("type") == "Freebie"
            ]

            # Filter vouchers client-side
            vouchers = [d for d in all_deals if d.get("type") == "Voucher"]

            # Fetch user profile if logged in with safety delay
            profile = None
            if self.api.username:
                import time

                time.sleep(1.5)
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
