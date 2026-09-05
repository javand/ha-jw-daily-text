"""Config flow for ha_jw_daily_text."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .api import LANGUAGE_CODE_MAP
from .const import DEFAULT_LANGUAGE, DOMAIN, SUPPORTED_LANGUAGES

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult


class JWTextConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for JW Daily Text."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="JW Daily Text",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required("language", default=DEFAULT_LANGUAGE): vol.In(
                    SUPPORTED_LANGUAGES
                )
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return JWTextOptionsFlowHandler(config_entry)


class JWTextOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for JW Daily Text."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        raw_lang = self.config_entry.options.get(
            "language",
            self.config_entry.data.get("language", DEFAULT_LANGUAGE),
        )
        current_lang = (
            LANGUAGE_CODE_MAP.get(raw_lang.lower(), DEFAULT_LANGUAGE)
            if isinstance(raw_lang, str)
            else DEFAULT_LANGUAGE
        )

        schema = vol.Schema(
            {
                vol.Required("language", default=current_lang): vol.In(
                    SUPPORTED_LANGUAGES
                )
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)


# Backward compatibility alias
BlueprintFlowHandler = JWTextConfigFlow
