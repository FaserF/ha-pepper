"""Deals-related sensors for Pepper integration."""

import statistics
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry

from ..const import (
    CONF_FILTER_KEYWORDS,
    CONF_FILTER_MAX_PRICE,
    CONF_FILTER_MERCHANTS,
    CONF_FILTER_MIN_TEMP,
    CONF_KEYWORDS,
    DEFAULT_FILTER_MIN_TEMP,
)
from ..coordinator import PepperDataUpdateCoordinator
from ..entity import PepperEntity

# Maximum number of deal entries to include in list state attributes.
MAX_DEALS_IN_ATTRS = 10

# Keys kept when a full deal dict is embedded in state attributes.
_SLIM_DEAL_KEYS = (
    "id",
    "title",
    "url",
    "price",
    "next_best_price",
    "temperature",
    "published_at",
    "picked_at",
    "voucher_code",
    "type",
    "status",
    "is_expired",
    "comment_count",
    "share_count",
    "merchant",
    "merchant_page_url",
    "submitter",
    "image_url",
    "groups",
    "temp_change",
)


def _slim_deal(deal: dict[str, Any]) -> dict[str, Any]:
    """Return a reduced deal dict without heavy fields (e.g. description)."""
    return {k: deal[k] for k in _SLIM_DEAL_KEYS if k in deal}


def _slim_deals(
    deals: list[dict[str, Any]], limit: int = MAX_DEALS_IN_ATTRS
) -> list[dict[str, Any]]:
    """Return a slimmed and capped list of deal dicts."""
    return [_slim_deal(d) for d in deals[:limit]]


class PepperTopDealsSensor(PepperEntity, SensorEntity):
    """Representation of a Pepper top deals sensor with feed statistics."""

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
        if not self.coordinator.data:
            return {}
        deals = self.coordinator.data.get("deals", [])
        freebies = self.coordinator.data.get("freebies", [])

        # Stats calculations
        temps = [
            d["temperature"]
            for d in deals
            if d.get("temperature") is not None
            and isinstance(d["temperature"], (int, float))
        ]
        prices = [
            d["price"]
            for d in deals
            if d.get("price") is not None
            and isinstance(d["price"], (int, float))
            and d["price"] > 0.0
        ]

        # Cheapest and hottest deals
        cheapest_deal = None
        priced_deals = [
            d
            for d in deals
            if d.get("price") is not None
            and isinstance(d["price"], (int, float))
            and d["price"] > 0.0
        ]
        if priced_deals:
            c_d = min(priced_deals, key=lambda d: d["price"])
            cheapest_deal = {"title": c_d.get("title"), "price": c_d.get("price")}

        hottest_deal = None
        if temps:
            h_d = max(
                [
                    d
                    for d in deals
                    if d.get("temperature") is not None
                    and isinstance(d["temperature"], (int, float))
                ],
                key=lambda d: d["temperature"],
            )
            hottest_deal = {
                "title": h_d.get("title"),
                "temperature": h_d.get("temperature"),
            }

        hottest_rising_deal = None
        rising_deals = [d for d in deals if d.get("temp_change", 0.0) > 0.0]
        if rising_deals:
            r_d = max(rising_deals, key=lambda d: d.get("temp_change", 0.0))
            hottest_rising_deal = {
                "title": r_d.get("title"),
                "temp_change": r_d.get("temp_change"),
            }

        # Merchant, submitter, groups stats
        merchant_stats: dict[str, int] = {}
        submitter_stats: dict[str, int] = {}
        group_stats: dict[str, int] = {}
        type_dist: dict[str, int] = {}
        for d in deals:
            m = d.get("merchant")
            if m:
                merchant_stats[m] = merchant_stats.get(m, 0) + 1
            s = d.get("submitter")
            if s:
                submitter_stats[s] = submitter_stats.get(s, 0) + 1
            for g in d.get("groups") or []:
                group_stats[g] = group_stats.get(g, 0) + 1
            t = d.get("type") or "Unknown"
            type_dist[t] = type_dist.get(t, 0) + 1

        top_merchant = (
            max(merchant_stats, key=lambda k: merchant_stats[k])
            if merchant_stats
            else None
        )
        top_submitter = (
            max(submitter_stats, key=lambda k: submitter_stats[k])
            if submitter_stats
            else None
        )
        top_group = (
            max(group_stats, key=lambda k: group_stats[k]) if group_stats else None
        )

        # Price errors count
        price_errors = 0
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
                price_errors += 1

        # Savings statistics
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

        expired_deals = len([d for d in deals if d.get("is_expired")])
        picked_deals = len(
            [d for d in deals if d.get("picked_at") and d["picked_at"] > 0]
        )

        return {
            "sort_mode": self.coordinator.sort_mode,
            "deals_count": len(deals),
            "deals": _slim_deals(deals),
            # Consolidated statistics
            "average_temperature": round(statistics.mean(temps), 1) if temps else None,
            "average_price": round(statistics.mean(prices), 2) if prices else None,
            "average_saving_percent": round(statistics.mean(pcts), 1) if pcts else None,
            "cheapest_deal": cheapest_deal,
            "hottest_deal": hottest_deal,
            "hottest_rising_deal": hottest_rising_deal,
            "discussion_count": len(
                [d for d in deals if d.get("type") == "Discussion"]
            ),
            "voucher_count": len([d for d in deals if d.get("type") == "Voucher"]),
            "freebie_count": len(freebies),
            "price_errors_count": price_errors,
            "expired_deals_count": expired_deals,
            "expired_deals_percentage": round((expired_deals / len(deals)) * 100, 1)
            if deals
            else 0.0,
            "picked_deals_count": picked_deals,
            "top_merchant": top_merchant,
            "top_submitter": top_submitter,
            "top_group": top_group,
            "deal_type_distribution": type_dist,
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
            "deals": _slim_deals(matching),
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
            "freebies": _slim_deals(freebies),
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
            "vouchers": _slim_deals(vouchers),
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
        return {"deal": _slim_deal(deal)} if deal else {}


class PepperGroupTopDealsSensor(PepperEntity, SensorEntity):
    """Sensor showing the top deal for a specific category/group."""

    _attr_icon = "mdi:tag-outline"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
        group: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._group = group
        self._attr_unique_id = (
            f"{entry.entry_id}_group_{group.lower().replace(' ', '_')}_top_deal"
        )
        self._attr_name = f"Top Deal - {group}"

    def _get_group_deals(self) -> list[dict[str, Any]]:
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        group_lower = self._group.lower()
        return [
            d
            for d in deals
            if any(g.lower() == group_lower for g in d.get("groups", []))
        ]

    @property
    def native_value(self) -> str | None:
        """Return the title of the top deal in this group."""
        deals = self._get_group_deals()
        if deals:
            return deals[0].get("title")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return dynamic group deal attributes."""
        deals = self._get_group_deals()
        return {
            "group": self._group,
            "deals_count": len(deals),
            "deals": _slim_deals(deals),
        }


class PepperGroupDealCountSensor(PepperEntity, SensorEntity):
    """Sensor showing the count of deals in a specific category/group."""

    _attr_icon = "mdi:numeric"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
        group: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._group = group
        self._attr_unique_id = (
            f"{entry.entry_id}_group_{group.lower().replace(' ', '_')}_deal_count"
        )
        self._attr_name = f"Deal Count - {group}"

    def _get_group_deals(self) -> list[dict[str, Any]]:
        deals = self.coordinator.data.get("deals", []) if self.coordinator.data else []
        group_lower = self._group.lower()
        return [
            d
            for d in deals
            if any(g.lower() == group_lower for g in d.get("groups", []))
        ]

    @property
    def native_value(self) -> int:
        """Return the count of deals in this group."""
        return len(self._get_group_deals())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return dynamic group deal attributes."""
        return {
            "group": self._group,
        }


class PepperSmartFilterDealsSensor(PepperEntity, SensorEntity):
    """Sensor showing count of deals matching the custom smart filter rules."""

    _attr_icon = "mdi:filter-check"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_smart_filter_deals"
        self._attr_name = "Smart Filter Deals"

    def _get_matching_deals(self) -> list[dict[str, Any]]:
        if not self.coordinator.data:
            return []
        deals = self.coordinator.data.get("deals", [])

        min_temp = self._entry.options.get(
            CONF_FILTER_MIN_TEMP,
            self._entry.data.get(CONF_FILTER_MIN_TEMP, DEFAULT_FILTER_MIN_TEMP),
        )
        max_price = self._entry.options.get(
            CONF_FILTER_MAX_PRICE,
            self._entry.data.get(CONF_FILTER_MAX_PRICE, 0.0),
        )
        raw_merchants = self._entry.options.get(
            CONF_FILTER_MERCHANTS,
            self._entry.data.get(CONF_FILTER_MERCHANTS, ""),
        )
        raw_keywords = self._entry.options.get(
            CONF_FILTER_KEYWORDS,
            self._entry.data.get(CONF_FILTER_KEYWORDS, ""),
        )

        merchants = [m.strip().lower() for m in raw_merchants.split(",") if m.strip()]
        keywords = [k.strip().lower() for k in raw_keywords.split(",") if k.strip()]

        matching = []
        for d in deals:
            temp = d.get("temperature")
            if temp is None or not isinstance(temp, (int, float)) or temp < min_temp:
                continue

            price = d.get("price")
            if max_price > 0.0:
                if (
                    price is None
                    or not isinstance(price, (int, float))
                    or price > max_price
                ):
                    continue

            if merchants:
                merchant = d.get("merchant")
                if not merchant or merchant.lower() not in merchants:
                    continue

            if keywords:
                title = (d.get("title") or "").lower()
                description = (d.get("description") or "").lower()
                if not any(k in title or k in description for k in keywords):
                    continue

            matching.append(d)
        return matching

    @property
    def native_value(self) -> int:
        """Return the count of matching deals."""
        return len(self._get_matching_deals())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return matching deals."""
        matching = self._get_matching_deals()
        return {
            "matches_count": len(matching),
            "deals": _slim_deals(matching),
        }


class PepperDynamicSearchSensor(PepperEntity, SensorEntity):
    """Sensor showing the current dynamic search query."""

    _attr_icon = "mdi:magnify"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_dynamic_search"
        self._attr_name = "Dynamic Search"

    @property
    def native_value(self) -> str | None:
        """Return the active query string."""
        return self.coordinator.dynamic_search_query

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return search results."""
        return {
            "query": self.coordinator.dynamic_search_query,
            "results_count": len(self.coordinator.dynamic_search_results),
            "deals": self.coordinator.dynamic_search_results[:MAX_DEALS_IN_ATTRS],
        }
