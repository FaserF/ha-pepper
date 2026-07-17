"""Binary sensor platform for Pepper integration."""

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_FILTER_KEYWORDS,
    CONF_FILTER_MAX_PRICE,
    CONF_FILTER_MERCHANTS,
    CONF_FILTER_MIN_TEMP,
    CONF_KEYWORDS,
    CONF_TEMP_THRESHOLD,
    DEFAULT_FILTER_MIN_TEMP,
    DEFAULT_TEMP_THRESHOLD,
    DOMAIN,
)
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
        PepperFreebieAvailableSensor(coordinator, entry),
        PepperVoucherAvailableSensor(coordinator, entry),
        PepperNewDealAvailableSensor(coordinator, entry),
        PepperExpirableDealAvailableSensor(coordinator, entry),
        PepperKeywordMatchAvailableSensor(coordinator, entry),
        PepperSuperHotDealAvailableSensor(coordinator, entry),
        PepperPriceErrorAvailableSensor(coordinator, entry),
        # Advanced Smart Filter
        PepperSmartFilterMatchSensor(coordinator, entry),
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


class PepperFreebieAvailableSensor(PepperEntity, BinarySensorEntity):
    """Binary sensor that turns ON if any freebies are currently available."""

    _attr_icon = "mdi:gift"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_freebie_available"
        self._attr_name = "Freebie Available"

    @property
    def is_on(self) -> bool:
        """Return True if freebies exist."""
        if not self.coordinator.data:
            return False
        return len(self.coordinator.data.get("freebies", [])) > 0


class PepperVoucherAvailableSensor(PepperEntity, BinarySensorEntity):
    """Binary sensor that turns ON if any vouchers are currently available."""

    _attr_icon = "mdi:ticket-percent"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_voucher_available"
        self._attr_name = "Voucher Available"

    @property
    def is_on(self) -> bool:
        """Return True if vouchers exist."""
        if not self.coordinator.data:
            return False
        return len(self.coordinator.data.get("vouchers", [])) > 0


class PepperNewDealAvailableSensor(PepperEntity, BinarySensorEntity):
    """Binary sensor that turns ON if any deals were published in the last 60 minutes."""

    _attr_icon = "mdi:new-box"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_new_deal_available"
        self._attr_name = "New Deal Available"

    @property
    def is_on(self) -> bool:
        """Return True if new deals exist."""
        if not self.coordinator.data:
            return False
        deals = self.coordinator.data.get("deals", [])
        from datetime import UTC, datetime

        now_ts = datetime.now(tz=UTC).timestamp()
        cutoff = now_ts - 3600
        return any(d.get("published_at") and d["published_at"] >= cutoff for d in deals)


class PepperExpirableDealAvailableSensor(PepperEntity, BinarySensorEntity):
    """Binary sensor that turns ON if any active (non-expired) deal in the feed has an expiration date."""

    _attr_icon = "mdi:calendar-clock"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_expirable_deal_available"
        self._attr_name = "Expirable Deal Available"

    @property
    def is_on(self) -> bool:
        """Return True if any expirable non-expired deal exists."""
        if not self.coordinator.data:
            return False
        deals = self.coordinator.data.get("deals", [])
        return any(d.get("expirable") and not d.get("is_expired") for d in deals)


class PepperKeywordMatchAvailableSensor(PepperEntity, BinarySensorEntity):
    """Binary sensor that turns ON if any active (non-expired) deal matches the configured keywords."""

    _attr_icon = "mdi:bell-alert"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_keyword_match_available"
        self._attr_name = "Keyword Match Available"

    def _get_keywords(self) -> list[str]:
        """Get configured keywords."""
        raw = self._entry.options.get(
            CONF_KEYWORDS, self._entry.data.get(CONF_KEYWORDS, "")
        )
        if not raw:
            return []
        return [k.strip().lower() for k in raw.split(",") if k.strip()]

    @property
    def is_on(self) -> bool:
        """Return True if any active deal matches the keywords."""
        keywords = self._get_keywords()
        if not keywords or not self.coordinator.data:
            return False
        deals = self.coordinator.data.get("deals", [])
        for deal in deals:
            if deal.get("is_expired"):
                continue
            title = (deal.get("title") or "").lower()
            description = (deal.get("description") or "").lower()
            if any(k in title or k in description for k in keywords):
                return True
        return False


class PepperSuperHotDealAvailableSensor(PepperEntity, BinarySensorEntity):
    """Binary sensor that turns ON if any deal temperature exceeds 500°."""

    _attr_icon = "mdi:fire"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_super_hot_deal_available"
        self._attr_name = "Super Hot Deal Available"

    @property
    def is_on(self) -> bool:
        """Return True if any deal has temperature >= 500."""
        if not self.coordinator.data:
            return False
        deals = self.coordinator.data.get("deals", [])
        for d in deals:
            temp = d.get("temperature")
            if temp is not None and isinstance(temp, (int, float)) and temp >= 500:
                return True
        return False


class PepperPriceErrorAvailableSensor(PepperEntity, BinarySensorEntity):
    """Binary sensor that turns ON if any active (non-expired) deal in the feed is a price error."""

    _attr_icon = "mdi:alert-decagram"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_price_error_available"
        self._attr_name = "Price Error Available"

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
    def is_on(self) -> bool:
        """Return True if any active price error exists."""
        return len(self._get_price_errors()) > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return price error deals."""
        errors = self._get_price_errors()
        return {
            "price_errors_count": len(errors),
            "deals": errors,
        }


class PepperSmartFilterMatchSensor(PepperEntity, BinarySensorEntity):
    """Binary sensor that turns ON if any deal matches all custom smart filter rules."""

    _attr_icon = "mdi:filter-check"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_smart_filter_match"
        self._attr_name = "Smart Filter Match"

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
    def is_on(self) -> bool:
        """Return True if any matching deals are found."""
        return len(self._get_matching_deals()) > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        matching = self._get_matching_deals()
        return {
            "matches_count": len(matching),
            "deals": matching,
        }
