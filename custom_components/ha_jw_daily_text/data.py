"""Custom types for ha_jw_daily_text."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import JWTextApiClient
    from .coordinator import JWDailyTextCoordinator


type IntegrationBlueprintConfigEntry = ConfigEntry[IntegrationBlueprintData]
type JWDailyTextConfigEntry = ConfigEntry[IntegrationBlueprintData]


@dataclass
class IntegrationBlueprintData:
    """Data for the JW Daily Text integration."""

    client: JWTextApiClient
    coordinator: JWDailyTextCoordinator
    integration: Integration | None = None
