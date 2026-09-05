# ruff: noqa: S101
"""Tests for JW Daily Text config flow and options flow."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from homeassistant import config_entries, data_entry_flow

from custom_components.ha_jw_daily_text.config_flow import (
    JWTextConfigFlow,
    JWTextOptionsFlowHandler,
)
from custom_components.ha_jw_daily_text.const import (
    DEFAULT_LANGUAGE,
    DOMAIN,
    SUPPORTED_LANGUAGES,
)


def test_config_flow_user_step_form() -> None:
    """Test showing the user configuration form with default language."""

    async def _run() -> None:
        flow = JWTextConfigFlow()
        flow.hass = MagicMock()

        result = await flow.async_step_user()
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["data_schema"] is not None

        schema = result["data_schema"].schema
        # Check language field is present and required
        lang_key = next(k for k in schema if k == "language")
        assert lang_key.default() == DEFAULT_LANGUAGE
        assert schema[lang_key].container == SUPPORTED_LANGUAGES

    asyncio.run(_run())


def test_config_flow_user_step_create_entry() -> None:
    """Test creating an entry when user input is valid."""

    async def _run() -> None:
        flow = JWTextConfigFlow()
        flow.hass = MagicMock()
        flow.context = {}
        flow.hass.config_entries.flow.async_progress_by_handler.return_value = []
        flow.hass.config_entries.async_entry_for_domain_unique_id.return_value = None

        result = await flow.async_step_user(user_input={"language": "lp-e"})
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == "JW Daily Text"
        assert result["data"] == {"language": "lp-e"}
        assert flow.unique_id == DOMAIN

    asyncio.run(_run())


def test_config_flow_user_step_already_configured() -> None:
    """Test aborting the flow if already configured."""

    async def _run() -> None:
        flow = JWTextConfigFlow()
        flow.hass = MagicMock()
        flow.context = {}
        flow.hass.config_entries.flow.async_progress_by_handler.return_value = []
        existing_entry = MagicMock()
        flow.hass.config_entries.async_entry_for_domain_unique_id.return_value = (
            existing_entry
        )

        with pytest.raises(data_entry_flow.AbortFlow) as exc_info:
            await flow.async_step_user(user_input={"language": "lp-e"})
        assert exc_info.value.reason == "already_configured"

    asyncio.run(_run())


def test_config_flow_async_get_options_flow() -> None:
    """Test obtaining the options flow handler from config flow."""
    mock_entry = MagicMock(spec=config_entries.ConfigEntry)
    options_flow = JWTextConfigFlow.async_get_options_flow(mock_entry)
    assert isinstance(options_flow, JWTextOptionsFlowHandler)
    assert options_flow.config_entry == mock_entry


def test_options_flow_init_step_form_default_data() -> None:
    """Test options flow shows form with default language from entry data."""

    async def _run() -> None:
        mock_entry = MagicMock(spec=config_entries.ConfigEntry)
        mock_entry.options = {}
        mock_entry.data = {"language": "lp-s"}

        options_flow = JWTextOptionsFlowHandler(mock_entry)
        options_flow.hass = MagicMock()

        result = await options_flow.async_step_init()
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "init"
        assert result["data_schema"] is not None

        schema = result["data_schema"].schema
        lang_key = next(k for k in schema if k == "language")
        assert lang_key.default() == "lp-s"
        assert schema[lang_key].container == SUPPORTED_LANGUAGES

    asyncio.run(_run())


def test_options_flow_init_step_form_default_options() -> None:
    """Test options flow prioritizing options over data."""

    async def _run() -> None:
        mock_entry = MagicMock(spec=config_entries.ConfigEntry)
        mock_entry.options = {"language": "lp-f"}
        mock_entry.data = {"language": "lp-e"}

        options_flow = JWTextOptionsFlowHandler(mock_entry)
        options_flow.hass = MagicMock()

        result = await options_flow.async_step_init()
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "init"

        schema = result["data_schema"].schema
        lang_key = next(k for k in schema if k == "language")
        assert lang_key.default() == "lp-f"

    asyncio.run(_run())


def test_options_flow_init_step_create_entry() -> None:
    """Test options flow updates options on user submit."""

    async def _run() -> None:
        mock_entry = MagicMock(spec=config_entries.ConfigEntry)
        mock_entry.options = {"language": "lp-e"}
        mock_entry.data = {"language": "lp-e"}

        options_flow = JWTextOptionsFlowHandler(mock_entry)
        options_flow.hass = MagicMock()

        result = await options_flow.async_step_init(user_input={"language": "lp-po"})
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == ""
        assert result["data"] == {"language": "lp-po"}

    asyncio.run(_run())


def test_translations_en_structure() -> None:
    """Test that en.json matches the required translations schema without URLs."""
    en_path = (
        Path(__file__).parent.parent
        / "custom_components"
        / "ha_jw_daily_text"
        / "translations"
        / "en.json"
    )
    with en_path.open(encoding="utf-8") as f:
        data = json.load(f)

    # Config step user
    assert "config" in data
    assert "step" in data["config"]
    assert "user" in data["config"]["step"]
    user_step = data["config"]["step"]["user"]
    assert user_step["title"] == "JW Daily Text"
    assert "description" in user_step
    assert "documentation_url" not in user_step["description"]
    assert user_step["data"]["language"] == "WOL Language"

    # Abort
    assert "abort" in data["config"]
    assert "already_configured" in data["config"]["abort"]

    # Options step init
    assert "options" in data
    assert "step" in data["options"]
    assert "init" in data["options"]["step"]
    init_step = data["options"]["step"]["init"]
    assert init_step["title"] == "JW Daily Text Options"
    assert init_step["data"]["language"] == "WOL Language"
