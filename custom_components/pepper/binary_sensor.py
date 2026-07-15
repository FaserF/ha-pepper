"""Binary sensor platform for Pepper integration."""

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_KEYWORDS, CONF_TEMP_THRESHOLD, DEFAULT_TEMP_THRESHOLD, DOMAIN
from .coordinator import PepperDataUpdateCoordinator
from .entity import PepperEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Pepper binary sensor platform."""
    coordinator: PepperDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = [
        PepperHighTempAlertSensor(coordinator, entry),
        PepperExpiredKeywordDealSensor(coordinator, entry),
    ]

    async_add_entities(entities, True)


class PepperHighTempAlertSensor(PepperEntity, BinarySensorEntity):
    """Binary sensor that turns ON when any deal exceeds the temperature threshold."""

    _attr_icon = "mdi:fire"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
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
            CONF_TEMP_THRESHOLD,
            self._entry.data.get(CONF_TEMP_THRESHOLD, DEFAULT_TEMP_THRESHOLD),
        )

    def _get_alert_deals(self) -> list[dict[str, Any]]:
        """Get list of deals exceeding the threshold."""
        threshold = self._get_threshold()
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        alerts = []
        for deal in deals:
            temp = deal.get("temperature")
            # Filter valid numbers that exceed or equal the threshold
            if (
                temp is not None
                and isinstance(temp, (int, float))
                and temp >= threshold
            ):
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


class PepperExpiredKeywordDealSensor(PepperEntity, BinarySensorEntity):
    """Binary sensor that turns ON when any keyword-matched deal has expired.

    Useful for automations that alert when a tracked deal is no longer
    available (e.g. ``is_expired=True`` or ``status != 'Activated'``).
    """

    _attr_icon = "mdi:bell-off"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_expired_keyword_deal"
        self._attr_name = "Expired Keyword Deal"

    def _get_keywords(self) -> list[str]:
        """Get configured keywords."""
        raw = self._entry.options.get(
            CONF_KEYWORDS, self._entry.data.get(CONF_KEYWORDS, "")
        )
        if not raw:
            return []
        return [k.strip().lower() for k in raw.split(",") if k.strip()]

    def _get_expired_keyword_deals(self) -> list[dict[str, Any]]:
        """Return keyword-matching deals that are expired."""
        keywords = self._get_keywords()
        if not keywords:
            return []
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        expired = []
        for deal in deals:
            title = (deal.get("title") or "").lower()
            description = (deal.get("description") or "").lower()
            if any(k in title or k in description for k in keywords):
                if deal.get("is_expired") or deal.get("status") not in (
                    None,
                    "Activated",
                ):
                    expired.append(deal)
        return expired

    @property
    def is_on(self) -> bool:
        """Return True if any keyword-matched deal has expired."""
        return len(self._get_expired_keyword_deals()) > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        expired = self._get_expired_keyword_deals()
        return {
            "keywords": self._get_keywords(),
            "expired_keyword_deals_count": len(expired),
            "deals": expired,
        }
