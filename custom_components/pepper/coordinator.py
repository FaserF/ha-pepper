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
        self._first_refresh = True
        self.last_latency: float | None = None
        self.last_error: str | None = None
        self._previous_deals: dict[str, float] = {}
        self.dynamic_search_query: str | None = None
        self.dynamic_search_results: list[dict[str, Any]] = []

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_interval_min),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Pepper API."""
        # Add a random jitter delay to evade anti-bot profiling
        jitter = random.uniform(2.0, 6.0)
        if self.api.username and self._first_refresh:
            # Extra delay on startup to prevent WAF rate-limiting immediately after config flow login
            jitter += 12.0
            self._first_refresh = False
        _LOGGER.debug("Waiting for random jitter delay of %.2fs", jitter)
        await asyncio.sleep(jitter)

        def _fetch_all_data() -> dict[str, Any]:
            # On the very first fetch, explicitly prime the session:
            # - If we already have serialized cookies (authenticated), just silently GET
            #   the homepage to refresh XSRF — no new login that would trigger the WAF.
            # - If we have no cookies yet (anonymous), do a full fetch_session.
            if self._first_refresh:
                self._first_refresh = False
                if self.api._session_authenticated:
                    _LOGGER.debug(
                        "First coordinator fetch: refreshing homepage only (session authenticated)"
                    )
                    self.api._refresh_homepage()
                else:
                    _LOGGER.debug(
                        "First coordinator fetch: no active session, fetching full session"
                    )
                    self.api.fetch_session()

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

            # Calculate temperature changes
            current_deals_temp = {}
            for d in all_deals:
                deal_id = d.get("id")
                temp = d.get("temperature")
                if deal_id is not None and temp is not None:
                    current_deals_temp[str(deal_id)] = float(temp)
                    prev_temp = self._previous_deals.get(str(deal_id))
                    if prev_temp is not None:
                        d["temp_change"] = round(float(temp) - prev_temp, 2)
                    else:
                        d["temp_change"] = 0.0
            self._previous_deals = current_deals_temp

            # Fetch user profile if logged in with safety delay
            profile = None
            if self.api.username:
                import time

                time.sleep(1.5)
                profile = self.api.get_user_profile()

            # Dynamic search execution
            if self.dynamic_search_query:
                import time

                time.sleep(1.5)
                try:
                    self.dynamic_search_results = self.api.search_deals(
                        self.dynamic_search_query
                    )
                except Exception as err:
                    _LOGGER.warning("Error fetching dynamic search deals: %s", err)
                    self.dynamic_search_results = []

            return {
                "deals": deals,
                "freebies": freebies,
                "vouchers": vouchers,
                "profile": profile,
            }

        import time

        start_time = time.monotonic()
        try:
            # Run the synchronous API calls in an executor thread
            res = await self.hass.async_add_executor_job(_fetch_all_data)
            self.last_latency = round(time.monotonic() - start_time, 2)
            self.last_error = None
            return res
        except Exception as err:
            self.last_latency = round(time.monotonic() - start_time, 2)
            self.last_error = str(err)
            _LOGGER.warning(
                "Error fetching Pepper data from platform %s: %s",
                self.api.platform,
                err,
                exc_info=True,
            )
            raise UpdateFailed(f"Error fetching Pepper data: {err}") from err
