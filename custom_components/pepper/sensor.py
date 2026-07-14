"""Sensor platform for Pepper integration."""

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_KEYWORDS, DOMAIN
from .coordinator import PepperDataUpdateCoordinator
from .entity import PepperEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Pepper sensor platform."""
    coordinator: PepperDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        PepperTopDealsSensor(coordinator, entry),
        PepperKeywordAlertsSensor(coordinator, entry),
    ]

    async_add_entities(entities, True)


class PepperTopDealsSensor(PepperEntity, SensorEntity):
    """Representation of a Pepper top deals sensor."""

    _attr_icon = "mdi:sale"

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_deals"
        self._attr_name = "Top Deals"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor (the title of the top deal)."""
        deals = self.coordinator.data
        if deals:
            return deals[0].get("title")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        deals = self.coordinator.data or []
        return {
            "sort_mode": self.coordinator.sort_mode,
            "deals_count": len(deals),
            "deals": deals,
        }


class PepperKeywordAlertsSensor(PepperEntity, SensorEntity):
    """Representation of a Pepper keyword alerts sensor."""

    _attr_icon = "mdi:bell-ring"
    # Disabled by default, user can enable it if they use keywords
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_keyword_alerts"
        self._attr_name = "Keyword Alerts"

    def _get_keywords(self) -> list[str]:
        """Get list of clean, lowercase keywords from configuration."""
        raw_keywords = self._entry.options.get(
            CONF_KEYWORDS, self._entry.data.get(CONF_KEYWORDS, "")
        )
        if not raw_keywords:
            return []
        return [k.strip().lower() for k in raw_keywords.split(",") if k.strip()]

    def _get_matching_deals(self) -> list[dict[str, Any]]:
        """Filter deals matching configured keywords."""
        keywords = self._get_keywords()
        if not keywords:
            return []

        deals = self.coordinator.data or []
        matching = []
        for deal in deals:
            title = (deal.get("title") or "").lower()
            description = (deal.get("description") or "").lower()

            # Match if any keyword is found in title or description
            if any(k in title or k in description for k in keywords):
                matching.append(deal)
        return matching

    @property
    def native_value(self) -> int:
        """Return the number of matching deals."""
        return len(self._get_matching_deals())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        matching = self._get_matching_deals()
        return {
            "keywords": self._get_keywords(),
            "matches_count": len(matching),
            "deals": matching,
        }
