# ruff: noqa: S101, PLR2004, SLF001
"""Tests for JW Daily Text sensor platform and entry setup."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import Platform

from custom_components.ha_jw_daily_text import (
    PLATFORMS,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ha_jw_daily_text.api import DailyTextEntry, JWDailyTextData
from custom_components.ha_jw_daily_text.const import DEFAULT_LANGUAGE, DOMAIN
from custom_components.ha_jw_daily_text.coordinator import JWDailyTextCoordinator
from custom_components.ha_jw_daily_text.data import IntegrationBlueprintData
from custom_components.ha_jw_daily_text.sensor import (
    JWDailyTextSensor,
    truncate_state,
)
from custom_components.ha_jw_daily_text.sensor import (
    async_setup_entry as async_setup_sensor_entry,
)


def _sample_daily_text_data(long_text: str | None = None) -> JWDailyTextData:
    """Return sample daily text data for testing."""
    default_text = (
        "Jehovah detests a devious person, but His close friendship is with"
        " the upright."
    )
    today_text = long_text if long_text is not None else default_text
    return JWDailyTextData(
        yesterday=DailyTextEntry(
            date="2026-09-03",
            day_and_date="Thursday, September 3",
            scripture_text="Yesterday scripture text.",
            scripture="Genesis 1:1",
            comments="Yesterday comments text.",
        ),
        today=DailyTextEntry(
            date="2026-09-04",
            day_and_date="Friday, September 4",
            scripture_text=today_text,
            scripture="Proverbs 3:32",
            comments="Today comments text.",
        ),
        tomorrow=DailyTextEntry(
            date="2026-09-05",
            day_and_date="Saturday, September 5",
            scripture_text="Tomorrow scripture text.",
            scripture="Revelation 21:4",
            comments="Tomorrow comments text.",
        ),
    )


def test_truncate_state_short_and_exact() -> None:
    """Test truncate_state returns unmodified string when length <= max_len."""
    short = "Short scripture"
    assert truncate_state(short) == short

    exact_255 = "A" * 255
    assert truncate_state(exact_255) == exact_255
    assert len(truncate_state(exact_255)) == 255


def test_truncate_state_long_string() -> None:
    """Test truncate_state truncates strings longer than max_len with ellipsis."""
    long_str = "A" * 300
    truncated = truncate_state(long_str)
    assert len(truncated) == 255
    assert truncated.endswith("…")
    assert truncated == ("A" * 254) + "…"


def test_truncate_state_custom_max_len() -> None:
    """Test truncate_state with custom max_len."""
    text = "Hello World"
    assert truncate_state(text, max_len=5) == "Hell…"
    assert len(truncate_state(text, max_len=5)) == 5
    assert truncate_state("Hi", max_len=5) == "Hi"


def test_sensor_state_truncation_and_attributes_text() -> None:
    """Test text sensor truncates state to 255 and stores full text in attributes."""
    long_text = "A" * 300
    mock_data = _sample_daily_text_data(long_text=long_text)
    coordinator = AsyncMock()
    coordinator.data = mock_data

    sensor = JWDailyTextSensor(
        coordinator=coordinator,
        target_day="today",
        field_type="text",
        name="JW Daily Text Today",
        unique_id="jw_daily_text_today",
    )

    # State truncated to 255 characters with ellipsis
    assert len(sensor.native_value) == 255
    assert sensor.native_value.endswith("…")
    assert sensor.unique_id == "jw_daily_text_today"
    assert sensor.name == "JW Daily Text Today"

    # Extra state attributes contain full untruncated text for TTS
    attrs = sensor.extra_state_attributes
    assert attrs["text"] == long_text
    assert attrs["scripture"] == "Proverbs 3:32"
    assert attrs["day_and_date"] == "Friday, September 4"
    assert attrs["date"] == "2026-09-04"


def test_sensor_state_truncation_and_attributes_comment() -> None:
    """Test comment sensor truncates state and provides TTS text attribute."""
    long_comment = "C" * 350
    mock_data = _sample_daily_text_data()
    mock_data.today.comments = long_comment
    coordinator = AsyncMock()
    coordinator.data = mock_data

    sensor = JWDailyTextSensor(
        coordinator=coordinator,
        target_day="today",
        field_type="comment",
        name="JW Daily Text Today Comment",
        unique_id="jw_daily_text_today_comment",
    )

    assert len(sensor.native_value) == 255
    assert sensor.native_value.endswith("…")
    assert sensor.unique_id == "jw_daily_text_today_comment"
    assert sensor.name == "JW Daily Text Today Comment"

    attrs = sensor.extra_state_attributes
    assert attrs["text"] == long_comment
    assert attrs["day_and_date"] == "Friday, September 4"
    assert attrs["date"] == "2026-09-04"
    # Scripture citation is not in comment attributes
    assert "scripture" not in attrs


def test_sensor_yesterday_and_tomorrow_data() -> None:
    """Test yesterday and tomorrow sensors retrieve respective target day data."""
    mock_data = _sample_daily_text_data()
    coordinator = AsyncMock()
    coordinator.data = mock_data

    yesterday_text_sensor = JWDailyTextSensor(
        coordinator=coordinator,
        target_day="yesterday",
        field_type="text",
        name="JW Daily Text Yesterday",
        unique_id="jw_daily_text_yesterday",
    )
    assert yesterday_text_sensor.native_value == "Yesterday scripture text."
    assert yesterday_text_sensor.extra_state_attributes["scripture"] == "Genesis 1:1"
    assert yesterday_text_sensor.extra_state_attributes["date"] == "2026-09-03"

    tomorrow_comment_sensor = JWDailyTextSensor(
        coordinator=coordinator,
        target_day="tomorrow",
        field_type="comment",
        name="JW Daily Text Tomorrow Comment",
        unique_id="jw_daily_text_tomorrow_comment",
    )
    assert tomorrow_comment_sensor.native_value == "Tomorrow comments text."
    assert (
        tomorrow_comment_sensor.extra_state_attributes["day_and_date"]
        == "Saturday, September 5"
    )
    assert tomorrow_comment_sensor.extra_state_attributes["date"] == "2026-09-05"


def test_sensor_coordinator_data_none() -> None:
    """Test sensor returns None and empty attributes when coordinator data is None."""
    coordinator = AsyncMock()
    coordinator.data = None

    sensor = JWDailyTextSensor(
        coordinator=coordinator,
        target_day="today",
        field_type="text",
        name="JW Daily Text Today",
        unique_id="jw_daily_text_today",
    )

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


def test_sensor_async_setup_entry() -> None:
    """Test async_setup_entry registers all 6 JW Daily Text sensors."""

    async def _run() -> None:
        hass = MagicMock()
        mock_coordinator = AsyncMock(spec=JWDailyTextCoordinator)
        mock_entry = MagicMock()
        mock_entry.runtime_data = IntegrationBlueprintData(
            client=MagicMock(),
            coordinator=mock_coordinator,
            integration=None,
        )

        added_entities = []

        def _add_entities(entities: list[JWDailyTextSensor]) -> None:
            added_entities.extend(entities)

        await async_setup_sensor_entry(hass, mock_entry, _add_entities)

        assert len(added_entities) == 6

        expected_entities = [
            ("jw_daily_text_today", "JW Daily Text Today", "today", "text"),
            (
                "jw_daily_text_today_comment",
                "JW Daily Text Today Comment",
                "today",
                "comment",
            ),
            (
                "jw_daily_text_yesterday",
                "JW Daily Text Yesterday",
                "yesterday",
                "text",
            ),
            (
                "jw_daily_text_yesterday_comment",
                "JW Daily Text Yesterday Comment",
                "yesterday",
                "comment",
            ),
            ("jw_daily_text_tomorrow", "JW Daily Text Tomorrow", "tomorrow", "text"),
            (
                "jw_daily_text_tomorrow_comment",
                "JW Daily Text Tomorrow Comment",
                "tomorrow",
                "comment",
            ),
        ]

        for idx, (uid, name, day, ftype) in enumerate(expected_entities):
            sensor = added_entities[idx]
            assert isinstance(sensor, JWDailyTextSensor)
            assert sensor.unique_id == uid
            assert sensor.name == name
            assert sensor._target_day == day
            assert sensor._field_type == ftype

    asyncio.run(_run())


def test_integration_init_setup_and_unload() -> None:
    """Test integration async_setup_entry and async_unload_entry lifecycle."""

    async def _run() -> None:
        hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.domain = DOMAIN
        mock_entry.data = {}
        mock_entry.options = {"language": "lp-s"}

        with (
            patch(
                "custom_components.ha_jw_daily_text.async_get_clientsession"
            ) as mock_session,
            patch("custom_components.ha_jw_daily_text.JWTextApiClient") as mock_api_cls,
            patch(
                "custom_components.ha_jw_daily_text.JWDailyTextCoordinator"
            ) as mock_coord_cls,
        ):
            mock_client = MagicMock()
            mock_api_cls.return_value = mock_client

            mock_coordinator = AsyncMock()
            mock_coord_cls.return_value = mock_coordinator

            hass.config_entries.async_forward_entry_setups = AsyncMock(
                return_value=True
            )
            hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

            # 1. Setup entry
            result = await async_setup_entry(hass, mock_entry)
            assert result is True

            # Verify API client created with options language
            mock_api_cls.assert_called_once_with(
                session=mock_session.return_value,
                language="lp-s",
            )

            # Verify coordinator instantiated and refreshed
            mock_coord_cls.assert_called_once_with(
                hass=hass,
                api_client=mock_client,
            )
            mock_coordinator.async_config_entry_first_refresh.assert_awaited_once()

            # Verify runtime_data set
            assert isinstance(mock_entry.runtime_data, IntegrationBlueprintData)
            assert mock_entry.runtime_data.client == mock_client
            assert mock_entry.runtime_data.coordinator == mock_coordinator

            # Verify forward setups to PLATFORMS ([Platform.SENSOR])
            assert PLATFORMS == [Platform.SENSOR]
            hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
                mock_entry,
                PLATFORMS,
            )

            # 2. Unload entry
            unload_result = await async_unload_entry(hass, mock_entry)
            assert unload_result is True
            hass.config_entries.async_unload_platforms.assert_awaited_once_with(
                mock_entry,
                PLATFORMS,
            )

    asyncio.run(_run())


def test_integration_init_setup_default_language() -> None:
    """Test integration async_setup_entry defaults to DEFAULT_LANGUAGE when not set."""

    async def _run() -> None:
        hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.domain = DOMAIN
        mock_entry.data = {}
        mock_entry.options = {}

        with (
            patch(
                "custom_components.ha_jw_daily_text.async_get_clientsession"
            ) as mock_session,
            patch("custom_components.ha_jw_daily_text.JWTextApiClient") as mock_api_cls,
            patch(
                "custom_components.ha_jw_daily_text.JWDailyTextCoordinator"
            ) as mock_coord_cls,
        ):
            mock_client = MagicMock()
            mock_api_cls.return_value = mock_client

            mock_coordinator = AsyncMock()
            mock_coord_cls.return_value = mock_coordinator

            hass.config_entries.async_forward_entry_setups = AsyncMock(
                return_value=True
            )

            result = await async_setup_entry(hass, mock_entry)
            assert result is True

            # Verify API client created with DEFAULT_LANGUAGE
            mock_api_cls.assert_called_once_with(
                session=mock_session.return_value,
                language=DEFAULT_LANGUAGE,
            )

    asyncio.run(_run())
