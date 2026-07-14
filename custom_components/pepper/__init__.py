"""The Pepper integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_PLATFORM,
    CONF_SORT_MODE,
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
    sort_mode = entry.options.get(CONF_SORT_MODE, entry.data.get(CONF_SORT_MODE, DEFAULT_SORT_MODE))
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

    api = PepperAPI(platform=platform)

    coordinator = PepperDataUpdateCoordinator(
        hass,
        api=api,
        sort_mode=sort_mode,
        update_interval_min=scan_interval,
    )

    # Initial data refresh
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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
