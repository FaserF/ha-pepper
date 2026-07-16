"""Diagnostics support for Pepper integration."""

from __future__ import annotations

import math
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_PASSWORD, CONF_USERNAME, DOMAIN
from .coordinator import PepperDataUpdateCoordinator

REDACT_KEYS = {
    CONF_PASSWORD,
    CONF_USERNAME,
    "password",
    "username",
    "cookies",
    "xsrf_token",
    "headers",
    "cookie",
    "authorization",
}


def _to_json_safe(obj: Any) -> Any:
    """Convert to JSON safe representation."""
    if isinstance(obj, bool) or obj is None:
        return obj
    if isinstance(obj, (int, str)):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return str(obj)
        return obj
    if isinstance(obj, (list, tuple, set)):
        return [_to_json_safe(i) for i in obj]
    if isinstance(obj, dict):
        return {str(k): _to_json_safe(v) for k, v in obj.items()}
    if hasattr(obj, "__dict__"):
        return _to_json_safe(obj.__dict__)
    return str(obj)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics."""
    try:
        coordinator: PepperDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
        data = coordinator.data
    except (KeyError, AttributeError):
        return {"error": "Coordinator not found"}

    diag: dict[str, Any] = {
        "config_entry": async_redact_data(dict(entry.data), REDACT_KEYS),
        "options": async_redact_data(dict(entry.options), REDACT_KEYS),
        "coordinator_last_update_success": coordinator.last_update_success,
    }

    if data:
        try:
            diag["coordinator_data"] = {
                "deals_count": len(data.get("deals", [])),
                "freebies_count": len(data.get("freebies", [])),
                "vouchers_count": len(data.get("vouchers", [])),
                "has_profile": data.get("profile") is not None,
            }
            if data.get("profile"):
                profile = data["profile"]
                diag["coordinator_data"]["profile"] = {
                    "username": "[REDACTED]" if profile.get("username") else None,
                    "id": "[REDACTED]" if profile.get("id") else None,
                }
        except Exception as err:
            diag["data_error"] = str(err)

    return _to_json_safe(diag)
