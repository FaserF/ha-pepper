"""Config flow for Pepper integration."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_KEYWORDS,
    CONF_LIMIT,
    CONF_PLATFORM,
    CONF_SORT_MODE,
    CONF_TEMP_THRESHOLD,
    DEFAULT_LIMIT,
    DEFAULT_PLATFORM,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SORT_MODE,
    DEFAULT_TEMP_THRESHOLD,
    DOMAIN,
    PLATFORMS_MAP,
)
from .pepper_api import PepperAPI


class PepperConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pepper."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate connection by doing a test fetch on the selected platform
            try:
                api = PepperAPI(platform=user_input[CONF_PLATFORM])
                await self.hass.async_add_executor_job(api.fetch_session)

                name = PLATFORMS_MAP.get(
                    user_input[CONF_PLATFORM], user_input[CONF_PLATFORM]
                )
                title = f"{name} ({user_input[CONF_SORT_MODE].capitalize()})"
                return self.async_create_entry(title=title, data=user_input)
            except Exception:
                errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_PLATFORM, default=DEFAULT_PLATFORM): vol.In(
                    PLATFORMS_MAP
                ),
                vol.Required(CONF_SORT_MODE, default=DEFAULT_SORT_MODE): vol.In(
                    ["hot", "new"]
                ),
                vol.Required(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
                vol.Optional(CONF_KEYWORDS, default=""): vol.Coerce(str),
                vol.Optional(
                    CONF_TEMP_THRESHOLD, default=DEFAULT_TEMP_THRESHOLD
                ): vol.Coerce(int),
                vol.Optional(CONF_LIMIT, default=DEFAULT_LIMIT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=100)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return PepperOptionsFlowHandler(config_entry)


class PepperOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Pepper options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SORT_MODE,
                    default=self.config_entry.options.get(
                        CONF_SORT_MODE,
                        self.config_entry.data.get(CONF_SORT_MODE, DEFAULT_SORT_MODE),
                    ),
                ): vol.In(["hot", "new"]),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL,
                        self.config_entry.data.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
                vol.Optional(
                    CONF_KEYWORDS,
                    default=self.config_entry.options.get(
                        CONF_KEYWORDS, self.config_entry.data.get(CONF_KEYWORDS, "")
                    ),
                ): vol.Coerce(str),
                vol.Optional(
                    CONF_TEMP_THRESHOLD,
                    default=self.config_entry.options.get(
                        CONF_TEMP_THRESHOLD,
                        self.config_entry.data.get(
                            CONF_TEMP_THRESHOLD, DEFAULT_TEMP_THRESHOLD
                        ),
                    ),
                ): vol.Coerce(int),
                vol.Optional(
                    CONF_LIMIT,
                    default=self.config_entry.options.get(
                        CONF_LIMIT,
                        self.config_entry.data.get(CONF_LIMIT, DEFAULT_LIMIT),
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
