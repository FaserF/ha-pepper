"""Sensor platform for Pepper integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_GROUPS, DOMAIN
from .coordinator import PepperDataUpdateCoordinator
from .sensors.account import PepperUserAccountSensor
from .sensors.deals import (
    PepperDynamicSearchSensor,
    PepperFeedDealCountSensor,
    PepperFreebiesSensor,
    PepperFreshestDealSensor,
    PepperGroupDealCountSensor,
    PepperGroupTopDealsSensor,
    PepperKeywordAlertsSensor,
    PepperSmartFilterDealsSensor,
    PepperTopDealsSensor,
    PepperVouchersSensor,
)
from .sensors.diagnostics import PepperAPIStatusSensor


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Pepper sensor platform."""
    coordinator: PepperDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        PepperTopDealsSensor(coordinator, entry),
        PepperFreebiesSensor(coordinator, entry),
        PepperFeedDealCountSensor(coordinator, entry),
        PepperFreshestDealSensor(coordinator, entry),
        # Disabled by default
        PepperKeywordAlertsSensor(coordinator, entry),
        PepperVouchersSensor(coordinator, entry),
        # Diagnostics
        PepperAPIStatusSensor(coordinator, entry),
        # Advanced features
        PepperSmartFilterDealsSensor(coordinator, entry),
        PepperDynamicSearchSensor(coordinator, entry),
    ]

    if coordinator.api.username:
        entities.extend(
            [
                PepperUserAccountSensor(coordinator, entry),
            ]
        )

    # Dynamic group/category sensors
    raw_groups = entry.options.get(CONF_GROUPS, entry.data.get(CONF_GROUPS, ""))
    if raw_groups:
        groups = [g.strip() for g in raw_groups.split(",") if g.strip()]
        for group in groups:
            entities.extend(
                [
                    PepperGroupTopDealsSensor(coordinator, entry, group),
                    PepperGroupDealCountSensor(coordinator, entry, group),
                ]
            )

    async_add_entities(entities, True)
