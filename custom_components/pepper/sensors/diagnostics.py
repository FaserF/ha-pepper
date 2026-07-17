"""Diagnostics status sensor for Pepper integration."""

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry

from ..coordinator import PepperDataUpdateCoordinator
from ..entity import PepperEntity


class PepperAPIStatusSensor(PepperEntity, SensorEntity):
    """Sensor showing the Pepper API status and latency diagnostics."""

    _attr_icon = "mdi:api"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: PepperDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id, coordinator.api.platform)
        self._attr_unique_id = f"{entry.entry_id}_api_status"
        self._attr_name = "API Status"

    @property
    def native_value(self) -> str:
        """Return the status."""
        return "Error" if self.coordinator.last_error else "Online"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return status attributes."""
        return {
            "latency": self.coordinator.last_latency,
            "last_error": self.coordinator.last_error,
            "last_update_success": self.coordinator.last_update_success,
        }
