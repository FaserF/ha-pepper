"""Sensor platform for Pepper integration."""

import logging
from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_KEYWORDS, DOMAIN
from .coordinator import PepperDataUpdateCoordinator
from .entity import PepperEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Pepper sensor platform."""
    coordinator: PepperDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        PepperTopDealsSensor(coordinator, entry),
        PepperFreebiesSensor(coordinator, entry),
        # Disabled by default
        PepperKeywordAlertsSensor(coordinator, entry),
        PepperVouchersSensor(coordinator, entry),
        PepperNewDealsCountSensor(coordinator, entry),
        PepperExpiredDealsCountSensor(coordinator, entry),
        PepperPickedDealsCountSensor(coordinator, entry),
        PepperTopMerchantSensor(coordinator, entry),
    ]

    if coordinator.api.username:
        entities.extend(
            [
                PepperUserThreadCountSensor(coordinator, entry),
                PepperUserCommentCountSensor(coordinator, entry),
            ]
        )

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
        if not self.coordinator.data:
            return None
        deals = self.coordinator.data.get("deals", [])
        if deals:
            return deals[0].get("title")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        return {
            "sort_mode": self.coordinator.sort_mode,
            "deals_count": len(deals),
            "deals": deals,
        }


class PepperKeywordAlertsSensor(PepperEntity, SensorEntity):
    """Representation of a Pepper keyword alerts sensor."""

    _attr_icon = "mdi:bell-ring"
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

        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
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


class PepperFreebiesSensor(PepperEntity, SensorEntity):
    """Representation of a Pepper freebies sensor."""

    _attr_icon = "mdi:gift"

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_freebies"
        self._attr_name = "Freebies"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor (the title of the top freebie)."""
        if not self.coordinator.data:
            return None
        freebies = self.coordinator.data.get("freebies", [])
        if freebies:
            return freebies[0].get("title")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        freebies = (
            self.coordinator.data.get("freebies", []) if self.coordinator.data else []
        )
        return {
            "freebies_count": len(freebies),
            "freebies": freebies,
        }


class PepperVouchersSensor(PepperEntity, SensorEntity):
    """Representation of a Pepper vouchers sensor."""

    _attr_icon = "mdi:ticket-percent"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_vouchers"
        self._attr_name = "Vouchers"

    @property
    def native_value(self) -> int:
        """Return the count of active vouchers."""
        if not self.coordinator.data:
            return 0
        return len(self.coordinator.data.get("vouchers", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        vouchers = (
            self.coordinator.data.get("vouchers", []) if self.coordinator.data else []
        )
        return {
            "vouchers_count": len(vouchers),
            "vouchers": vouchers,
        }


class PepperNewDealsCountSensor(PepperEntity, SensorEntity):
    """Sensor that counts deals published within the last hour."""

    _attr_icon = "mdi:new-box"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_new_deals_count"
        self._attr_name = "New Deals (Last Hour)"

    def _get_new_deals(self) -> list[dict[str, Any]]:
        """Return deals published in the last 60 minutes."""
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        now_ts = datetime.now(tz=UTC).timestamp()
        cutoff = now_ts - 3600  # 1 hour in seconds
        return [
            d for d in deals if d.get("published_at") and d["published_at"] >= cutoff
        ]

    @property
    def native_value(self) -> int:
        """Return count of deals published in the last hour."""
        return len(self._get_new_deals())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        new_deals = self._get_new_deals()
        return {
            "new_deals_count": len(new_deals),
            "deals": new_deals,
        }


class PepperExpiredDealsCountSensor(PepperEntity, SensorEntity):
    """Sensor that counts currently expired deals in the feed."""

    _attr_icon = "mdi:timer-off-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_expired_deals_count"
        self._attr_name = "Expired Deals"

    def _get_expired_deals(self) -> list[dict[str, Any]]:
        """Return deals flagged as expired."""
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        return [d for d in deals if d.get("is_expired")]

    @property
    def native_value(self) -> int:
        """Return count of expired deals."""
        return len(self._get_expired_deals())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        expired = self._get_expired_deals()
        return {
            "expired_count": len(expired),
            "deals": expired,
        }


class PepperPickedDealsCountSensor(PepperEntity, SensorEntity):
    """Sensor that counts deals that have been featured/picked by editors."""

    _attr_icon = "mdi:star-circle"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_picked_deals_count"
        self._attr_name = "Picked Deals"

    def _get_picked_deals(self) -> list[dict[str, Any]]:
        """Return deals that have been featured/picked (pickedAt > 0)."""
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        return [d for d in deals if d.get("picked_at") and d["picked_at"] > 0]

    @property
    def native_value(self) -> int:
        """Return count of featured/picked deals."""
        return len(self._get_picked_deals())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        picked = self._get_picked_deals()
        return {
            "picked_count": len(picked),
            "deals": picked,
        }


class PepperTopMerchantSensor(PepperEntity, SensorEntity):
    """Sensor showing the merchant with the most deals in the current feed."""

    _attr_icon = "mdi:store"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_top_merchant"
        self._attr_name = "Top Merchant"

    def _get_merchant_stats(self) -> dict[str, int]:
        """Count deals per merchant in the current feed."""
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        stats: dict[str, int] = {}
        for deal in deals:
            merchant = deal.get("merchant")
            if merchant:
                stats[merchant] = stats.get(merchant, 0) + 1
        return stats

    @property
    def native_value(self) -> str | None:
        """Return the merchant name with the most deals."""
        stats = self._get_merchant_stats()
        if not stats:
            return None
        return max(stats, key=lambda k: stats[k])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        stats = self._get_merchant_stats()
        top = self.native_value
        top_count = stats.get(top, 0) if top else 0
        return {
            "top_merchant": top,
            "top_merchant_deal_count": top_count,
            "merchant_deal_counts": stats,
        }


class PepperUserThreadCountSensor(PepperEntity, SensorEntity):
    """Sensor showing the number of threads/deals the user has submitted."""

    _attr_icon = "mdi:post"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_user_thread_count"
        self._attr_name = "User Thread Count"

    @property
    def native_value(self) -> int | None:
        """Return the number of threads posted by the user."""
        if not self.coordinator.data:
            return None
        profile = self.coordinator.data.get("profile")
        if profile:
            return profile.get("threadCount")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        profile = self.coordinator.data.get("profile") if self.coordinator.data else {}
        return {
            "username": (profile or {}).get("username"),
            "user_id": (profile or {}).get("userId"),
        }


class PepperUserCommentCountSensor(PepperEntity, SensorEntity):
    """Sensor showing the number of comments the user has posted."""

    _attr_icon = "mdi:comment-multiple"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_user_comment_count"
        self._attr_name = "User Comment Count"

    @property
    def native_value(self) -> int | None:
        """Return the number of comments posted by the user."""
        if not self.coordinator.data:
            return None
        profile = self.coordinator.data.get("profile")
        if profile:
            return profile.get("commentCount")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        profile = self.coordinator.data.get("profile") if self.coordinator.data else {}
        return {
            "username": (profile or {}).get("username"),
            "user_id": (profile or {}).get("userId"),
        }
