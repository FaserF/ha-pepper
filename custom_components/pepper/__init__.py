import logging
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)

_LOGGER = logging.getLogger(__name__)

from .const import (
    CONF_LIMIT,
    CONF_PASSWORD,
    CONF_PLATFORM,
    CONF_SORT_MODE,
    CONF_USERNAME,
    DEFAULT_LIMIT,
    DEFAULT_PLATFORM,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SORT_MODE,
    DOMAIN,
)
from .coordinator import PepperDataUpdateCoordinator
from .pepper_api import PepperAPI

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pepper from a config entry."""
    platform = entry.data.get(CONF_PLATFORM, DEFAULT_PLATFORM)
    sort_mode = entry.options.get(
        CONF_SORT_MODE, entry.data.get(CONF_SORT_MODE, DEFAULT_SORT_MODE)
    )
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )

    username = entry.options.get(CONF_USERNAME, entry.data.get(CONF_USERNAME))
    password = entry.options.get(CONF_PASSWORD, entry.data.get(CONF_PASSWORD))

    cookies = entry.data.get("cookies")
    xsrf_token = entry.data.get("xsrf_token")
    headers = entry.data.get("headers")

    if username != entry.data.get(CONF_USERNAME):
        cookies = None
        xsrf_token = None
        headers = None

    _LOGGER.debug(
        "Setting up entry %s. Username: %s. Cookies: %s. Has Token: %s. Has Headers: %s",
        entry.entry_id,
        username,
        len(cookies) if cookies else None,
        xsrf_token is not None,
        headers is not None,
    )

    api = PepperAPI(
        platform=platform,
        username=username,
        password=password,
        cookies=cookies,
        xsrf_token=xsrf_token,
        headers=headers,
    )

    limit = entry.options.get(CONF_LIMIT, entry.data.get(CONF_LIMIT, DEFAULT_LIMIT))

    coordinator = PepperDataUpdateCoordinator(
        hass,
        api=api,
        sort_mode=sort_mode,
        update_interval_min=scan_interval,
        limit=limit,
    )

    # Initial data refresh
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the search service/action
    async def async_search_deals_service(call: ServiceCall) -> ServiceResponse:
        """Search deals service."""
        query = call.data["query"]
        deals = await hass.async_add_executor_job(api.search_deals, query)
        from typing import cast

        return cast(ServiceResponse, {"deals": deals})

    hass.services.async_register(
        DOMAIN,
        "search",
        async_search_deals_service,
        schema=vol.Schema(
            {
                vol.Required("query"): str,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )

    # Register the refresh service/action
    async def async_refresh_service(call: ServiceCall) -> None:
        """Refresh data coordinator."""
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        "refresh",
        async_refresh_service,
    )

    # Register listener for options updates
    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options updates."""
    await hass.config_entries.async_reload(entry.entry_id)
