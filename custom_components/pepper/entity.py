"""Base Pepper entity class."""

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PLATFORMS_MAP
from .coordinator import PepperDataUpdateCoordinator


class PepperEntity(CoordinatorEntity[PepperDataUpdateCoordinator]):
    """Base representation of a Pepper entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry_id: str,
        platform: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._platform = platform

        platform_name = PLATFORMS_MAP.get(platform, platform)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=platform_name,
            manufacturer="Pepper Group",
            entry_type=DeviceEntryType.SERVICE,
        )
