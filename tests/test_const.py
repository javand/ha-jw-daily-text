# ruff: noqa: S101
"""Test constants and manifest for ha_jw_daily_text."""

import json
from pathlib import Path

from custom_components.ha_jw_daily_text.const import (
    DEFAULT_LANGUAGE,
    DOMAIN,
    LOGGER,
    SUPPORTED_LANGUAGES,
)


def test_constants() -> None:
    """Test constants values."""
    assert DOMAIN == "ha_jw_daily_text"
    assert DEFAULT_LANGUAGE == "lp-e"
    assert SUPPORTED_LANGUAGES == {
        "lp-e": "English",
        "lp-s": "Spanish",
        "lp-f": "French",
        "lp-x": "German",
        "lp-po": "Portuguese",
    }
    assert LOGGER.name == "custom_components.ha_jw_daily_text"


def test_manifest() -> None:
    """Test manifest.json values."""
    manifest_path = (
        Path(__file__).parent.parent
        / "custom_components"
        / "ha_jw_daily_text"
        / "manifest.json"
    )
    with manifest_path.open(encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["domain"] == "ha_jw_daily_text"
    assert manifest["name"] == "JW Daily Text"
