# ruff: noqa: S101, SLF001
"""Tests for JWDailyTextCoordinator and midnight schedule."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

from custom_components.ha_jw_daily_text.api import (
    DailyTextEntry,
    JWDailyTextData,
    JWTextApiClient,
    JWTextApiClientCommunicationError,
    JWTextApiClientError,
)
from custom_components.ha_jw_daily_text.coordinator import (
    BlueprintDataUpdateCoordinator,
    JWDailyTextCoordinator,
)


def _sample_daily_text_data() -> JWDailyTextData:
    """Return sample daily text data."""
    return JWDailyTextData(
        yesterday=DailyTextEntry(
            date="2026-09-03",
            day_and_date="Thursday, September 3",
            scripture_text="Yesterday text.",
            scripture="Genesis 1:1",
            comments="Yesterday comments.",
        ),
        today=DailyTextEntry(
            date="2026-09-04",
            day_and_date="Friday, September 4",
            scripture_text="Today text.",
            scripture="Proverbs 3:32",
            comments="Today comments.",
        ),
        tomorrow=DailyTextEntry(
            date="2026-09-05",
            day_and_date="Saturday, September 5",
            scripture_text="Tomorrow text.",
            scripture="Revelation 21:4",
            comments="Tomorrow comments.",
        ),
    )


def test_coordinator_update_success() -> None:
    """Test successful data update and midnight scheduling."""

    async def _run() -> None:
        hass = MagicMock()
        mock_api = AsyncMock(spec=JWTextApiClient)
        mock_data = _sample_daily_text_data()
        mock_api.async_get_daily_text_data.return_value = mock_data

        fixed_now = datetime(2026, 9, 4, 10, 0, 0, tzinfo=UTC)
        coordinator = JWDailyTextCoordinator(hass, mock_api)

        with (
            patch(
                "custom_components.ha_jw_daily_text.coordinator.dt_util.now",
                return_value=fixed_now,
            ),
            patch(
                "custom_components.ha_jw_daily_text.coordinator.async_track_point_in_time"
            ) as mock_track,
        ):
            data = await coordinator._async_update_data()

            assert data == mock_data
            assert data.today.date == "2026-09-04"
            assert data.today.scripture == "Proverbs 3:32"
            assert coordinator._retry_count == 0
            mock_api.async_get_daily_text_data.assert_awaited_once_with(
                fixed_now.date()
            )
            mock_track.assert_called_once()

    asyncio.run(_run())


def test_coordinator_midnight_schedule_calculation() -> None:
    """Test midnight schedule calculation and canceling previous timer."""

    async def _run() -> None:
        hass = MagicMock()
        mock_api = AsyncMock(spec=JWTextApiClient)
        coordinator = JWDailyTextCoordinator(hass, mock_api)

        # Mock previous timer cancel callback
        mock_unsub = MagicMock()
        coordinator._unsub_midnight_timer = mock_unsub

        fixed_now = datetime(2026, 9, 4, 23, 15, 0, tzinfo=UTC)
        expected_midnight = dt_util.start_of_local_day(
            fixed_now + timedelta(days=1)
        ) + timedelta(seconds=5)

        with (
            patch(
                "custom_components.ha_jw_daily_text.coordinator.dt_util.now",
                return_value=fixed_now,
            ),
            patch(
                "custom_components.ha_jw_daily_text.coordinator.async_track_point_in_time"
            ) as mock_track,
        ):
            coordinator._schedule_next_midnight()

            # Verify existing unsub was called
            mock_unsub.assert_called_once()
            # Verify new timer was registered with 5-second buffer
            mock_track.assert_called_once_with(
                hass,
                coordinator._async_scheduled_update,
                expected_midnight,
            )

    asyncio.run(_run())


def test_coordinator_retry_backoff_on_communication_error_no_cache() -> None:
    """Test retry backoff on communication error without cached data."""

    async def _run() -> None:
        hass = MagicMock()
        mock_api = AsyncMock(spec=JWTextApiClient)
        mock_api.async_get_daily_text_data.side_effect = (
            JWTextApiClientCommunicationError("Network unreachable")
        )

        coordinator = JWDailyTextCoordinator(hass, mock_api)
        coordinator.data = None

        fixed_now = datetime(2026, 9, 4, 12, 0, 0, tzinfo=UTC)

        with (
            patch(
                "custom_components.ha_jw_daily_text.coordinator.dt_util.now",
                return_value=fixed_now,
            ),
            patch(
                "custom_components.ha_jw_daily_text.coordinator.async_track_point_in_time"
            ) as mock_track,
            pytest.raises(UpdateFailed),
        ):
            await coordinator._async_update_data()

        # retry_count = 1 -> min(2**1, 30) = 2 minutes
        assert coordinator._retry_count == 1
        expected_retry_time = fixed_now + timedelta(minutes=2)
        mock_track.assert_called_once_with(
            hass,
            coordinator._async_scheduled_update,
            expected_retry_time,
        )

    asyncio.run(_run())


def test_coordinator_retry_backoff_exponential_cap() -> None:
    """Test exponential backoff progression capped at 30 minutes."""

    async def _run() -> None:
        hass = MagicMock()
        mock_api = AsyncMock(spec=JWTextApiClient)
        mock_api.async_get_daily_text_data.side_effect = (
            JWTextApiClientCommunicationError("Network down")
        )

        cached_data = _sample_daily_text_data()
        coordinator = JWDailyTextCoordinator(hass, mock_api)
        coordinator.data = cached_data

        fixed_now = datetime(2026, 9, 4, 12, 0, 0, tzinfo=UTC)
        expected_backoffs = [2, 4, 8, 16, 30, 30]

        with (
            patch(
                "custom_components.ha_jw_daily_text.coordinator.dt_util.now",
                return_value=fixed_now,
            ),
            patch(
                "custom_components.ha_jw_daily_text.coordinator.async_track_point_in_time"
            ) as mock_track,
        ):
            for idx, expected_minutes in enumerate(expected_backoffs, start=1):
                mock_track.reset_mock()
                data = await coordinator._async_update_data()
                # Cached data is returned
                assert data == cached_data
                assert coordinator._retry_count == idx
                expected_retry_time = fixed_now + timedelta(minutes=expected_minutes)
                mock_track.assert_called_once_with(
                    hass,
                    coordinator._async_scheduled_update,
                    expected_retry_time,
                )

    asyncio.run(_run())


def test_coordinator_retry_preserves_cached_data() -> None:
    """Test that communication failure preserves existing cached data."""

    async def _run() -> None:
        hass = MagicMock()
        mock_api = AsyncMock(spec=JWTextApiClient)
        cached_data = _sample_daily_text_data()
        mock_api.async_get_daily_text_data.return_value = cached_data

        coordinator = JWDailyTextCoordinator(hass, mock_api)

        with patch(
            "custom_components.ha_jw_daily_text.coordinator.async_track_point_in_time"
        ):
            # Initial success
            data = await coordinator._async_update_data()
            assert data == cached_data
            coordinator.data = data

            # Network failure occurs on next update
            mock_api.async_get_daily_text_data.side_effect = (
                JWTextApiClientCommunicationError("Temporary WOL outage")
            )
            data_after_error = await coordinator._async_update_data()

            assert data_after_error == cached_data
            assert coordinator._retry_count == 1

    asyncio.run(_run())


def test_coordinator_resets_retry_count_on_success() -> None:
    """Test that retry count is reset to zero after successful update."""

    async def _run() -> None:
        hass = MagicMock()
        mock_api = AsyncMock(spec=JWTextApiClient)
        mock_data = _sample_daily_text_data()
        mock_api.async_get_daily_text_data.return_value = mock_data

        coordinator = JWDailyTextCoordinator(hass, mock_api)
        coordinator._retry_count = 5

        with patch(
            "custom_components.ha_jw_daily_text.coordinator.async_track_point_in_time"
        ):
            await coordinator._async_update_data()
            assert coordinator._retry_count == 0

    asyncio.run(_run())


def test_coordinator_generic_api_error_raises_update_failed() -> None:
    """Test non-communication API errors raise UpdateFailed directly."""

    async def _run() -> None:
        hass = MagicMock()
        mock_api = AsyncMock(spec=JWTextApiClient)
        mock_api.async_get_daily_text_data.side_effect = JWTextApiClientError(
            "Unexpected error"
        )

        coordinator = JWDailyTextCoordinator(hass, mock_api)
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    asyncio.run(_run())


def test_coordinator_async_scheduled_update() -> None:
    """Test _async_scheduled_update invokes async_refresh."""

    async def _run() -> None:
        hass = MagicMock()
        mock_api = AsyncMock(spec=JWTextApiClient)
        coordinator = JWDailyTextCoordinator(hass, mock_api)
        coordinator.async_refresh = AsyncMock()

        await coordinator._async_scheduled_update(datetime.now(UTC))
        coordinator.async_refresh.assert_awaited_once()

    asyncio.run(_run())


def test_coordinator_async_setup_midnight_schedule() -> None:
    """Test async_setup_midnight_schedule invokes _schedule_next_midnight."""

    async def _run() -> None:
        hass = MagicMock()
        mock_api = AsyncMock(spec=JWTextApiClient)
        coordinator = JWDailyTextCoordinator(hass, mock_api)

        with patch.object(coordinator, "_schedule_next_midnight") as mock_schedule:
            coordinator.async_setup_midnight_schedule()
            mock_schedule.assert_called_once()

    asyncio.run(_run())


def test_coordinator_async_shutdown() -> None:
    """Test async_shutdown cancels midnight and retry timers."""

    async def _run() -> None:
        hass = MagicMock()
        mock_api = AsyncMock(spec=JWTextApiClient)
        coordinator = JWDailyTextCoordinator(hass, mock_api)

        mock_midnight_unsub = MagicMock()
        mock_retry_unsub = MagicMock()
        coordinator._unsub_midnight_timer = mock_midnight_unsub
        coordinator._unsub_retry_timer = mock_retry_unsub

        await coordinator.async_shutdown()

        mock_midnight_unsub.assert_called_once()
        mock_retry_unsub.assert_called_once()
        assert coordinator._unsub_midnight_timer is None
        assert coordinator._unsub_retry_timer is None

    asyncio.run(_run())


def test_backward_compatibility_alias() -> None:
    """Test BlueprintDataUpdateCoordinator alias matches JWDailyTextCoordinator."""
    assert BlueprintDataUpdateCoordinator is JWDailyTextCoordinator
