"""Binary sensor platform for Pepper integration."""
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_TEMP_THRESHOLD, DEFAULT_TEMP_THRESHOLD, DOMAIN
from .coordinator import PepperDataUpdateCoordinator
from .entity import PepperEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Pepper binary sensor platform."""
    coordinator: PepperDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        PepperHighTempAlertSensor(coordinator, entry)
    ]

    async_add_entities(entities, True)


class PepperHighTempAlertSensor(PepperEntity, BinarySensorEntity):
    """Representation of a Pepper high temperature alert binary sensor."""

    _attr_icon = "mdi:fire"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    # Disabled by default
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_high_temp_alert"
        self._attr_name = "High Temperature Alert"

    def _get_threshold(self) -> int:
        """Get configured temperature threshold."""
        return self._entry.options.get(
            CONF_TEMP_THRESHOLD, self._entry.data.get(CONF_TEMP_THRESHOLD, DEFAULT_TEMP_THRESHOLD)
        )

    def _get_alert_deals(self) -> list[dict[str, Any]]:
        """Get list of deals exceeding the threshold."""
        threshold = self._get_threshold()
        deals = self.coordinator.data or []
        alerts = []
        for deal in deals:
            temp = deal.get("temperature")
            # Filter valid numbers that exceed or equal the threshold
            if temp is not None and isinstance(temp, (int, float)) and temp >= threshold:
                alerts.append(deal)
        return alerts

    @property
    def is_on(self) -> bool:
        """Return True if any deal exceeds the temperature threshold."""
        return len(self._get_alert_deals()) > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        alerts = self._get_alert_deals()
        return {
            "temp_threshold": self._get_threshold(),
            "alert_deals_count": len(alerts),
            "deals": alerts,
        }
