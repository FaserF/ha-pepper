"""Config flow for Pepper integration."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import callback

from .const import (
    CONF_FILTER_KEYWORDS,
    CONF_FILTER_MAX_PRICE,
    CONF_FILTER_MERCHANTS,
    CONF_FILTER_MIN_TEMP,
    CONF_GROUPS,
    CONF_KEYWORDS,
    CONF_LIMIT,
    CONF_PASSWORD,
    CONF_PLATFORM,
    CONF_SORT_MODE,
    CONF_TEMP_THRESHOLD,
    CONF_USERNAME,
    DEFAULT_FILTER_MIN_TEMP,
    DEFAULT_LIMIT,
    DEFAULT_PLATFORM,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SORT_MODE,
    DEFAULT_TEMP_THRESHOLD,
    DOMAIN,
    PLATFORMS_MAP,
)
from .pepper_api import PepperAPI


class PepperConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for Pepper."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate connection by doing a test fetch on the selected platform
            try:
                # Validate credentials and establish session
                api = PepperAPI(
                    platform=user_input[CONF_PLATFORM],
                    username=user_input.get(CONF_USERNAME),
                    password=user_input.get(CONF_PASSWORD),
                )
                await self.hass.async_add_executor_job(api.fetch_session)

                # Store the verified session cookies, xsrf token, and headers to avoid double-login during entry setup
                user_input["cookies"] = api.dump_session_cookies()
                user_input["xsrf_token"] = api.xsrf_token
                user_input["headers"] = api._headers

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
                vol.Optional(CONF_GROUPS, default=""): vol.Coerce(str),
                vol.Optional(
                    CONF_TEMP_THRESHOLD, default=DEFAULT_TEMP_THRESHOLD
                ): vol.Coerce(int),
                vol.Optional(CONF_LIMIT, default=DEFAULT_LIMIT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=50)
                ),
                vol.Optional(CONF_USERNAME, default=""): vol.Coerce(str),
                vol.Optional(CONF_PASSWORD, default=""): vol.Coerce(str),
                vol.Optional(
                    CONF_FILTER_MIN_TEMP, default=DEFAULT_FILTER_MIN_TEMP
                ): vol.Coerce(int),
                vol.Optional(CONF_FILTER_MAX_PRICE, default=0.0): vol.Coerce(float),
                vol.Optional(CONF_FILTER_MERCHANTS, default=""): vol.Coerce(str),
                vol.Optional(CONF_FILTER_KEYWORDS, default=""): vol.Coerce(str),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return PepperOptionsFlowHandler()


class PepperOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Pepper options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input.get(CONF_USERNAME, "")
            password = user_input.get(CONF_PASSWORD, "")
            platform = self.config_entry.data.get(CONF_PLATFORM, DEFAULT_PLATFORM)

            try:
                # Validate credentials and establish session if provided
                api = PepperAPI(
                    platform=platform,
                    username=username if username else None,
                    password=password if password else None,
                )
                await self.hass.async_add_executor_job(api.fetch_session)

                # Store the verified session info back into config entry data
                new_data = dict(self.config_entry.data)
                new_data[CONF_USERNAME] = username
                new_data[CONF_PASSWORD] = password
                new_data["cookies"] = api.dump_session_cookies()
                new_data["xsrf_token"] = api.xsrf_token
                new_data["headers"] = api._headers

                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )

                # Save remaining options
                return self.async_create_entry(title="", data=user_input)
            except Exception:
                errors["base"] = "cannot_connect"

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
                    CONF_GROUPS,
                    default=self.config_entry.options.get(
                        CONF_GROUPS, self.config_entry.data.get(CONF_GROUPS, "")
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
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
                vol.Optional(
                    CONF_USERNAME,
                    default=self.config_entry.options.get(
                        CONF_USERNAME, self.config_entry.data.get(CONF_USERNAME, "")
                    ),
                ): vol.Coerce(str),
                vol.Optional(
                    CONF_PASSWORD,
                    default=self.config_entry.options.get(
                        CONF_PASSWORD, self.config_entry.data.get(CONF_PASSWORD, "")
                    ),
                ): vol.Coerce(str),
                vol.Optional(
                    CONF_FILTER_MIN_TEMP,
                    default=self.config_entry.options.get(
                        CONF_FILTER_MIN_TEMP,
                        self.config_entry.data.get(
                            CONF_FILTER_MIN_TEMP, DEFAULT_FILTER_MIN_TEMP
                        ),
                    ),
                ): vol.Coerce(int),
                vol.Optional(
                    CONF_FILTER_MAX_PRICE,
                    default=self.config_entry.options.get(
                        CONF_FILTER_MAX_PRICE,
                        self.config_entry.data.get(CONF_FILTER_MAX_PRICE, 0.0),
                    ),
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_FILTER_MERCHANTS,
                    default=self.config_entry.options.get(
                        CONF_FILTER_MERCHANTS,
                        self.config_entry.data.get(CONF_FILTER_MERCHANTS, ""),
                    ),
                ): vol.Coerce(str),
                vol.Optional(
                    CONF_FILTER_KEYWORDS,
                    default=self.config_entry.options.get(
                        CONF_FILTER_KEYWORDS,
                        self.config_entry.data.get(CONF_FILTER_KEYWORDS, ""),
                    ),
                ): vol.Coerce(str),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
