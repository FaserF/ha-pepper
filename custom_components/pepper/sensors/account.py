"""User account sensor for Pepper integration."""

from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry

from ..coordinator import PepperDataUpdateCoordinator
from ..entity import PepperEntity


class PepperUserAccountSensor(PepperEntity, SensorEntity):
    """Consolidated representation of a Pepper user account."""

    _attr_icon = "mdi:account"

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_user_account"
        self._attr_name = "User Account"

    @property
    def native_value(self) -> str | None:
        """Return the username of the logged in user."""
        if not self.coordinator.data:
            return None
        profile = self.coordinator.data.get("profile")
        if profile:
            return profile.get("username")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return user account details."""
        if not self.coordinator.data:
            return {}
        profile = self.coordinator.data.get("profile")
        if not profile:
            return {}

        created_ts = profile.get("createdAt")
        account_age_days = None
        created_at_date = None
        if created_ts:
            now_ts = datetime.now(tz=UTC).timestamp()
            account_age_days = max(0, int((now_ts - created_ts) // 86400))
            created_at_date = datetime.fromtimestamp(created_ts, tz=UTC).isoformat()

        avatar_url = None
        avatar = profile.get("avatar")
        if avatar and avatar.get("path") and avatar.get("name"):
            avatar_url = f"{self.coordinator.api.image_host}/{avatar['path']}/{avatar['name']}/re/100x100/qt/60/{avatar['name']}.jpg"

        return {
            "user_id": profile.get("userId"),
            "email": profile.get("email"),
            "avatar_url": avatar_url,
            "thread_count": profile.get("threadCount"),
            "comment_count": profile.get("commentCount"),
            "badge_count": len(profile.get("badges") or []),
            "badges": profile.get("badges") or [],
            "account_age_days": account_age_days,
            "created_at": created_at_date,
        }
