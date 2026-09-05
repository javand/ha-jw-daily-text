"""Sensor platform for ha_jw_daily_text."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import JWDailyTextCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .api import DailyTextEntry
    from .data import IntegrationBlueprintConfigEntry


def truncate_state(value: str, max_len: int = 255) -> str:
    """Truncate string to max length for HA state."""
    if len(value) <= max_len:
        return value
    if max_len <= 1:
        return value[:max_len]
    return value[: max_len - 1] + "…"


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: IntegrationBlueprintConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: JWDailyTextCoordinator = (
        entry.runtime_data.coordinator
        if hasattr(entry.runtime_data, "coordinator")
        else entry.runtime_data
    )

    sensors = [
        JWDailyTextSensor(
            coordinator=coordinator,
            target_day="today",
            field_type="text",
            name="JW Daily Text Today",
            unique_id="jw_daily_text_today",
        ),
        JWDailyTextSensor(
            coordinator=coordinator,
            target_day="today",
            field_type="comment",
            name="JW Daily Text Today Comment",
            unique_id="jw_daily_text_today_comment",
        ),
        JWDailyTextSensor(
            coordinator=coordinator,
            target_day="yesterday",
            field_type="text",
            name="JW Daily Text Yesterday",
            unique_id="jw_daily_text_yesterday",
        ),
        JWDailyTextSensor(
            coordinator=coordinator,
            target_day="yesterday",
            field_type="comment",
            name="JW Daily Text Yesterday Comment",
            unique_id="jw_daily_text_yesterday_comment",
        ),
        JWDailyTextSensor(
            coordinator=coordinator,
            target_day="tomorrow",
            field_type="text",
            name="JW Daily Text Tomorrow",
            unique_id="jw_daily_text_tomorrow",
        ),
        JWDailyTextSensor(
            coordinator=coordinator,
            target_day="tomorrow",
            field_type="comment",
            name="JW Daily Text Tomorrow Comment",
            unique_id="jw_daily_text_tomorrow_comment",
        ),
    ]

    async_add_entities(sensors)


class JWDailyTextSensor(CoordinatorEntity[JWDailyTextCoordinator], SensorEntity):
    """Representation of a JW Daily Text sensor."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: JWDailyTextCoordinator,
        target_day: str,
        field_type: str,
        name: str,
        unique_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._target_day = target_day
        self._field_type = field_type
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_icon = (
            "mdi:book-open-variant"
            if field_type == "text"
            else "mdi:comment-text-outline"
        )

        entry_id = getattr(getattr(coordinator, "config_entry", None), "entry_id", None)
        domain = getattr(getattr(coordinator, "config_entry", None), "domain", DOMAIN)
        if entry_id:
            self._attr_device_info = DeviceInfo(
                identifiers={(domain, entry_id)},
                name="JW Daily Text",
                manufacturer="Watchtower",
            )

    @property
    def _entry_data(self) -> DailyTextEntry | None:
        """Return the DailyTextEntry for this sensor's target day."""
        if self.coordinator.data is None:
            return None
        return getattr(self.coordinator.data, self._target_day, None)

    @property
    def native_value(self) -> str | None:
        """Return state truncated to 255 chars."""
        entry = self._entry_data
        if entry is None:
            return None
        val = entry.scripture_text if self._field_type == "text" else entry.comments
        if val is None:
            return None
        return truncate_state(val)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes with full text for TTS."""
        entry = self._entry_data
        if entry is None:
            return {}

        if self._field_type == "text":
            return {
                "text": entry.scripture_text,
                "scripture": entry.scripture,
                "day_and_date": entry.day_and_date,
                "date": entry.date,
            }

        return {
            "text": entry.comments,
            "day_and_date": entry.day_and_date,
            "date": entry.date,
        }


# Backward compatibility alias
IntegrationBlueprintSensor = JWDailyTextSensor
