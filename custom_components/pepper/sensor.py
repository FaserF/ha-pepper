"""Sensor platform for Pepper integration."""

import logging
import statistics
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
        PepperFeedDealCountSensor(coordinator, entry),
        PepperFreshestDealSensor(coordinator, entry),
        # Disabled by default
        PepperKeywordAlertsSensor(coordinator, entry),
        PepperVouchersSensor(coordinator, entry),
        PepperNewDealsCountSensor(coordinator, entry),
        PepperExpiredDealsCountSensor(coordinator, entry),
        PepperPickedDealsCountSensor(coordinator, entry),
        PepperTopMerchantSensor(coordinator, entry),
        PepperAverageTemperatureSensor(coordinator, entry),
        PepperCheapestDealSensor(coordinator, entry),
        PepperHottestDealTempSensor(coordinator, entry),
        PepperDealTypeDistributionSensor(coordinator, entry),
        PepperDealsWithVoucherCountSensor(coordinator, entry),
        PepperFreebieCountSensor(coordinator, entry),
        PepperMostCommentedDealSensor(coordinator, entry),
        PepperMostSharedDealSensor(coordinator, entry),
        PepperBestPriceSavingSensor(coordinator, entry),
        PepperBestPriceSavingPercentSensor(coordinator, entry),
        PepperAverageSavingPercentSensor(coordinator, entry),
        PepperAveragePriceSensor(coordinator, entry),
        PepperDiscussionCountSensor(coordinator, entry),
        PepperVoucherCountSensor(coordinator, entry),
        PepperExpiredDealsPercentageSensor(coordinator, entry),
        PepperTopSubmitterSensor(coordinator, entry),
        PepperTopGroupSensor(coordinator, entry),
        PepperHottestDealTitleSensor(coordinator, entry),
        PepperPriceErrorsSensor(coordinator, entry),
    ]

    if coordinator.api.username:
        entities.extend(
            [
                PepperUserThreadCountSensor(coordinator, entry),
                PepperUserCommentCountSensor(coordinator, entry),
                PepperUserAccountAgeDaysSensor(coordinator, entry),
                PepperUserBadgeCountSensor(coordinator, entry),
                PepperUserEmailSensor(coordinator, entry),
                PepperUserAvatarSensor(coordinator, entry),
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


class PepperFeedDealCountSensor(PepperEntity, SensorEntity):
    """Sensor showing the total number of deals in the current main feed."""

    _attr_icon = "mdi:numeric"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_feed_deal_count"
        self._attr_name = "Feed Deal Count"

    @property
    def native_value(self) -> int:
        """Return the count of deals in the feed."""
        if not self.coordinator.data:
            return 0
        return len(self.coordinator.data.get("deals", []))


class PepperFreshestDealSensor(PepperEntity, SensorEntity):
    """Sensor showing the title of the newest/freshest deal in the feed."""

    _attr_icon = "mdi:clock-outline"

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_freshest_deal"
        self._attr_name = "Freshest Deal"

    def _get_freshest_deal(self) -> dict[str, Any] | None:
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        if not deals:
            return None
        return max(deals, key=lambda d: d.get("published_at") or 0)

    @property
    def native_value(self) -> str | None:
        """Return the title of the freshest deal."""
        deal = self._get_freshest_deal()
        return deal.get("title") if deal else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return details of the freshest deal."""
        deal = self._get_freshest_deal()
        return {"deal": deal} if deal else {}


class PepperAverageTemperatureSensor(PepperEntity, SensorEntity):
    """Sensor showing the average temperature of the deals in the feed."""

    _attr_icon = "mdi:thermometer"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_average_temp"
        self._attr_name = "Average Temperature"

    @property
    def native_value(self) -> float | None:
        """Return the average temperature."""
        if not self.coordinator.data:
            return None
        deals = self.coordinator.data.get("deals", [])
        temps = [
            d["temperature"]
            for d in deals
            if d.get("temperature") is not None
            and isinstance(d["temperature"], (int, float))
        ]
        return round(statistics.mean(temps), 1) if temps else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return statistics on deal temperature."""
        if not self.coordinator.data:
            return {}
        deals = self.coordinator.data.get("deals", [])
        temps = [
            d["temperature"]
            for d in deals
            if d.get("temperature") is not None
            and isinstance(d["temperature"], (int, float))
        ]
        if not temps:
            return {}
        return {
            "min_temp": min(temps),
            "max_temp": max(temps),
            "median_temp": round(statistics.median(temps), 1),
            "std_dev": round(statistics.stdev(temps), 2) if len(temps) > 1 else 0.0,
        }


class PepperCheapestDealSensor(PepperEntity, SensorEntity):
    """Sensor showing the cheapest deal price in the feed."""

    _attr_icon = "mdi:cash-minus"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_cheapest_deal"
        self._attr_name = "Cheapest Deal"

    def _get_cheapest_deal(self) -> dict[str, Any] | None:
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        priced_deals = [
            d
            for d in deals
            if d.get("price") is not None and isinstance(d["price"], (int, float))
        ]
        if not priced_deals:
            return None
        return min(priced_deals, key=lambda d: d["price"])

    @property
    def native_value(self) -> float | None:
        """Return price of the cheapest deal."""
        deal = self._get_cheapest_deal()
        return deal.get("price") if deal else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return cheapest deal object."""
        deal = self._get_cheapest_deal()
        return {"deal": deal} if deal else {}


class PepperHottestDealTempSensor(PepperEntity, SensorEntity):
    """Sensor showing the temperature of the hottest deal in the feed."""

    _attr_icon = "mdi:fire-circle"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_hottest_temp"
        self._attr_name = "Hottest Deal Temperature"

    def _get_hottest_deal(self) -> dict[str, Any] | None:
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        temps = [
            d
            for d in deals
            if d.get("temperature") is not None
            and isinstance(d["temperature"], (int, float))
        ]
        if not temps:
            return None
        return max(temps, key=lambda d: d["temperature"])

    @property
    def native_value(self) -> float | None:
        """Return the temperature value."""
        deal = self._get_hottest_deal()
        return deal.get("temperature") if deal else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return hottest deal details."""
        deal = self._get_hottest_deal()
        return {"deal": deal} if deal else {}


class PepperDealTypeDistributionSensor(PepperEntity, SensorEntity):
    """Sensor that counts deals by their type."""

    _attr_icon = "mdi:chart-pie"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_type_distribution"
        self._attr_name = "Deal Type Distribution"

    def _get_distribution(self) -> dict[str, int]:
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        dist: dict[str, int] = {}
        for d in deals:
            t = d.get("type") or "Unknown"
            dist[t] = dist.get(t, 0) + 1
        return dist

    @property
    def native_value(self) -> str | None:
        """Return the most frequent deal type."""
        dist = self._get_distribution()
        if not dist:
            return None
        return max(dist, key=lambda k: dist[k])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return full type counts."""
        return {"distribution": self._get_distribution()}


class PepperDealsWithVoucherCountSensor(PepperEntity, SensorEntity):
    """Sensor that counts deals that have a voucher code in the main feed."""

    _attr_icon = "mdi:ticket-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_deals_with_voucher_count"
        self._attr_name = "Deals with Voucher Count"

    def _get_deals_with_voucher(self) -> list[dict[str, Any]]:
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        return [d for d in deals if d.get("voucher_code")]

    @property
    def native_value(self) -> int:
        """Return counts."""
        return len(self._get_deals_with_voucher())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the list of deals."""
        return {"deals": self._get_deals_with_voucher()}


class PepperFreebieCountSensor(PepperEntity, SensorEntity):
    """Sensor showing integer count of freebies available."""

    _attr_icon = "mdi:gift-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_freebie_count"
        self._attr_name = "Freebie Count"

    @property
    def native_value(self) -> int:
        """Return count."""
        if not self.coordinator.data:
            return 0
        return len(self.coordinator.data.get("freebies", []))


class PepperMostCommentedDealSensor(PepperEntity, SensorEntity):
    """Sensor showing the deal with the most comments."""

    _attr_icon = "mdi:message-reply-text"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_most_commented_deal"
        self._attr_name = "Most Commented Deal"

    def _get_most_commented(self) -> dict[str, Any] | None:
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        if not deals:
            return None
        return max(deals, key=lambda d: d.get("comment_count") or 0)

    @property
    def native_value(self) -> str | None:
        """Return title."""
        deal = self._get_most_commented()
        return deal.get("title") if deal else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return deal attributes."""
        deal = self._get_most_commented()
        return {"deal": deal} if deal else {}


class PepperMostSharedDealSensor(PepperEntity, SensorEntity):
    """Sensor showing the deal with the most shares."""

    _attr_icon = "mdi:share-variant"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_most_shared_deal"
        self._attr_name = "Most Shared Deal"

    def _get_most_shared(self) -> dict[str, Any] | None:
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        if not deals:
            return None
        return max(deals, key=lambda d: d.get("share_count") or 0)

    @property
    def native_value(self) -> str | None:
        """Return title."""
        deal = self._get_most_shared()
        return deal.get("title") if deal else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return deal attributes."""
        deal = self._get_most_shared()
        return {"deal": deal} if deal else {}


class PepperBestPriceSavingSensor(PepperEntity, SensorEntity):
    """Sensor showing the highest absolute price saving (next_best_price - price)."""

    _attr_icon = "mdi:tag-minus"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_best_saving"
        self._attr_name = "Best Saving (Absolute)"

    def _get_savings(self) -> list[tuple[float, dict[str, Any]]]:
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        savings = []
        for d in deals:
            p = d.get("price")
            nbp = d.get("next_best_price")
            if (
                p is not None
                and nbp is not None
                and isinstance(p, (int, float))
                and isinstance(nbp, (int, float))
            ):
                diff = nbp - p
                if diff > 0:
                    savings.append((round(diff, 2), d))
        return savings

    @property
    def native_value(self) -> float | None:
        """Return saving amount."""
        savings = self._get_savings()
        if not savings:
            return None
        return max(savings, key=lambda s: s[0])[0]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return deal with highest saving."""
        savings = self._get_savings()
        if not savings:
            return {}
        best = max(savings, key=lambda s: s[0])
        return {"deal": best[1], "saving_amount": best[0]}


class PepperBestPriceSavingPercentSensor(PepperEntity, SensorEntity):
    """Sensor showing the highest percentage price saving."""

    _attr_icon = "mdi:percent-outline"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_best_saving_percent"
        self._attr_name = "Best Saving (Percent)"

    def _get_savings_percent(self) -> list[tuple[float, dict[str, Any]]]:
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        savings = []
        for d in deals:
            p = d.get("price")
            nbp = d.get("next_best_price")
            if (
                p is not None
                and nbp is not None
                and isinstance(p, (int, float))
                and isinstance(nbp, (int, float))
                and nbp > 0
            ):
                pct = ((nbp - p) / nbp) * 100
                if pct > 0:
                    savings.append((round(pct, 1), d))
        return savings

    @property
    def native_value(self) -> float | None:
        """Return saving percent."""
        savings = self._get_savings_percent()
        if not savings:
            return None
        return max(savings, key=lambda s: s[0])[0]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return deal with highest saving."""
        savings = self._get_savings_percent()
        if not savings:
            return {}
        best = max(savings, key=lambda s: s[0])
        return {"deal": best[1], "saving_percent": best[0]}


class PepperUserAccountAgeDaysSensor(PepperEntity, SensorEntity):
    """Sensor showing the user's account age in days."""

    _attr_icon = "mdi:calendar-account"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_user_account_age"
        self._attr_name = "User Account Age (Days)"

    @property
    def native_value(self) -> int | None:
        """Return count of days."""
        if not self.coordinator.data:
            return None
        profile = self.coordinator.data.get("profile")
        if profile and profile.get("createdAt"):
            created_ts = profile["createdAt"]
            now_ts = datetime.now(tz=UTC).timestamp()
            diff_sec = now_ts - created_ts
            return max(0, int(diff_sec // 86400))
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return date formatted."""
        profile = self.coordinator.data.get("profile") if self.coordinator.data else {}
        if profile and profile.get("createdAt"):
            dt = datetime.fromtimestamp(profile["createdAt"], tz=UTC)
            return {"created_at_date": dt.isoformat()}
        return {}


class PepperUserBadgeCountSensor(PepperEntity, SensorEntity):
    """Sensor showing count of badges earned by the user."""

    _attr_icon = "mdi:trophy-variant"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_user_badge_count"
        self._attr_name = "User Badge Count"

    @property
    def native_value(self) -> int | None:
        """Return counts."""
        if not self.coordinator.data:
            return None
        profile = self.coordinator.data.get("profile")
        if profile:
            badges = profile.get("badges") or []
            return len(badges)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return badges list."""
        profile = self.coordinator.data.get("profile") if self.coordinator.data else {}
        if profile:
            return {"badges": profile.get("badges") or []}
        return {}


class PepperAverageSavingPercentSensor(PepperEntity, SensorEntity):
    """Sensor showing the average saving percentage of the deals in the feed."""

    _attr_icon = "mdi:percent"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_average_saving_percent"
        self._attr_name = "Average Saving Percent"

    @property
    def native_value(self) -> float | None:
        """Return the average saving percentage."""
        if not self.coordinator.data:
            return None
        deals = self.coordinator.data.get("deals", [])
        pcts = []
        for d in deals:
            p = d.get("price")
            nbp = d.get("next_best_price")
            if (
                p is not None
                and nbp is not None
                and isinstance(p, (int, float))
                and isinstance(nbp, (int, float))
                and nbp > 0
            ):
                pct = ((nbp - p) / nbp) * 100
                if pct > 0:
                    pcts.append(pct)
        return round(statistics.mean(pcts), 1) if pcts else None


class PepperAveragePriceSensor(PepperEntity, SensorEntity):
    """Sensor showing the average price of the deals in the feed."""

    _attr_icon = "mdi:cash"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_average_price"
        self._attr_name = "Average Price"

    @property
    def native_value(self) -> float | None:
        """Return the average price."""
        if not self.coordinator.data:
            return None
        deals = self.coordinator.data.get("deals", [])
        prices = [
            d["price"]
            for d in deals
            if d.get("price") is not None and isinstance(d["price"], (int, float))
        ]
        return round(statistics.mean(prices), 2) if prices else None


class PepperDiscussionCountSensor(PepperEntity, SensorEntity):
    """Sensor showing the number of discussion threads in the feed."""

    _attr_icon = "mdi:forum"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_discussion_count"
        self._attr_name = "Discussion Count"

    @property
    def native_value(self) -> int:
        """Return the count of discussions."""
        if not self.coordinator.data:
            return 0
        deals = self.coordinator.data.get("deals", [])
        return len([d for d in deals if d.get("type") == "Discussion"])


class PepperVoucherCountSensor(PepperEntity, SensorEntity):
    """Sensor showing the number of voucher threads in the main feed."""

    _attr_icon = "mdi:ticket-percent"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_voucher_count"
        self._attr_name = "Voucher Count"

    @property
    def native_value(self) -> int:
        """Return the count of vouchers."""
        if not self.coordinator.data:
            return 0
        deals = self.coordinator.data.get("deals", [])
        return len([d for d in deals if d.get("type") == "Voucher"])


class PepperExpiredDealsPercentageSensor(PepperEntity, SensorEntity):
    """Sensor showing the percentage of expired deals in the feed."""

    _attr_icon = "mdi:percent"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_expired_deals_percentage"
        self._attr_name = "Expired Deals Percentage"

    @property
    def native_value(self) -> float | None:
        """Return the percentage of expired deals."""
        if not self.coordinator.data:
            return None
        deals = self.coordinator.data.get("deals", [])
        if not deals:
            return 0.0
        expired = len([d for d in deals if d.get("is_expired")])
        return round((expired / len(deals)) * 100, 1)


class PepperTopSubmitterSensor(PepperEntity, SensorEntity):
    """Sensor showing the top submitter in the feed."""

    _attr_icon = "mdi:account-star"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_top_submitter"
        self._attr_name = "Top Submitter"

    def _get_submitter_stats(self) -> dict[str, int]:
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        stats: dict[str, int] = {}
        for d in deals:
            sub = d.get("submitter")
            if sub:
                stats[sub] = stats.get(sub, 0) + 1
        return stats

    @property
    def native_value(self) -> str | None:
        """Return top submitter username."""
        stats = self._get_submitter_stats()
        if not stats:
            return None
        return max(stats, key=lambda k: stats[k])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return submitter statistics."""
        stats = self._get_submitter_stats()
        top = self.native_value
        return {
            "top_submitter": top,
            "top_submitter_count": stats.get(top or "", 0),
            "submitter_counts": stats,
        }


class PepperTopGroupSensor(PepperEntity, SensorEntity):
    """Sensor showing the most frequent category/group in the feed."""

    _attr_icon = "mdi:folder-star"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_top_group"
        self._attr_name = "Top Group"

    def _get_group_stats(self) -> dict[str, int]:
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        stats: dict[str, int] = {}
        for d in deals:
            for g in d.get("groups") or []:
                stats[g] = stats.get(g, 0) + 1
        return stats

    @property
    def native_value(self) -> str | None:
        """Return top group path."""
        stats = self._get_group_stats()
        if not stats:
            return None
        return max(stats, key=lambda k: stats[k])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return group statistics."""
        stats = self._get_group_stats()
        top = self.native_value
        return {
            "top_group": top,
            "top_group_count": stats.get(top or "", 0),
            "group_counts": stats,
        }


class PepperHottestDealTitleSensor(PepperEntity, SensorEntity):
    """Sensor showing the title of the hottest deal in the feed."""

    _attr_icon = "mdi:fire-circle"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_hottest_deal_title"
        self._attr_name = "Hottest Deal Title"

    def _get_hottest_deal(self) -> dict[str, Any] | None:
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        temps = [
            d
            for d in deals
            if d.get("temperature") is not None
            and isinstance(d["temperature"], (int, float))
        ]
        if not temps:
            return None
        return max(temps, key=lambda d: d["temperature"])

    @property
    def native_value(self) -> str | None:
        """Return title of hottest deal."""
        deal = self._get_hottest_deal()
        return deal.get("title") if deal else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return deal details."""
        deal = self._get_hottest_deal()
        return {"deal": deal} if deal else {}


class PepperUserEmailSensor(PepperEntity, SensorEntity):
    """Sensor showing the user's email."""

    _attr_icon = "mdi:email"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_user_email"
        self._attr_name = "User Email"

    @property
    def native_value(self) -> str | None:
        """Return user email."""
        if not self.coordinator.data:
            return None
        profile = self.coordinator.data.get("profile")
        if profile:
            return profile.get("email")
        return None


class PepperUserAvatarSensor(PepperEntity, SensorEntity):
    """Sensor showing the user's avatar URL."""

    _attr_icon = "mdi:account-circle"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_user_avatar"
        self._attr_name = "User Avatar"

    @property
    def native_value(self) -> str | None:
        """Return user avatar URL."""
        if not self.coordinator.data:
            return None
        profile = self.coordinator.data.get("profile")
        if profile and profile.get("avatar"):
            avatar = profile["avatar"]
            if avatar.get("path") and avatar.get("name"):
                return f"{self.coordinator.api.image_host}/{avatar['path']}/{avatar['name']}/re/100x100/qt/60/{avatar['name']}.jpg"
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return avatar components."""
        if not self.coordinator.data:
            return {}
        profile = self.coordinator.data.get("profile")
        if profile and profile.get("avatar"):
            return {"avatar": profile["avatar"]}
        return {}


class PepperPriceErrorsSensor(PepperEntity, SensorEntity):
    """Sensor that counts active (non-expired) price error deals in the feed."""

    _attr_icon = "mdi:alert-decagram"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_price_errors"
        self._attr_name = "Price Errors"

    def _get_price_errors(self) -> list[dict[str, Any]]:
        """Get active price error deals."""
        if not self.coordinator.data:
            return []
        deals = self.coordinator.data.get("deals", [])
        errors = []
        for d in deals:
            if d.get("is_expired"):
                continue
            title = (d.get("title") or "").lower()
            description = (d.get("description") or "").lower()
            groups = [g.lower() for g in d.get("groups") or []]
            if (
                "preisfehler" in title
                or "preisfehler" in description
                or "preisfehler" in groups
            ):
                errors.append(d)
        return errors

    @property
    def native_value(self) -> int:
        """Return count of active price error deals."""
        return len(self._get_price_errors())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return price error deals."""
        errors = self._get_price_errors()
        return {
            "price_errors_count": len(errors),
            "deals": errors,
        }
