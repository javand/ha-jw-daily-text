"""Custom integration to integrate JW Daily Text with Home Assistant."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import JWTextApiClient
from .const import DEFAULT_LANGUAGE
from .coordinator import JWDailyTextCoordinator
from .data import IntegrationBlueprintData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import IntegrationBlueprintConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IntegrationBlueprintConfigEntry,
) -> bool:
    """Set up JW Daily Text from a config entry."""
    language = entry.options.get(
        "language",
        entry.data.get("language", DEFAULT_LANGUAGE),
    )
    session = async_get_clientsession(hass)
    client = JWTextApiClient(session=session, language=language)

    coordinator = JWDailyTextCoordinator(hass=hass, api_client=client)
    await coordinator.async_config_entry_first_refresh()

    integration = None
    try:
        integration = async_get_loaded_integration(hass, entry.domain)
    except Exception:  # noqa: BLE001
        integration = None

    entry.runtime_data = IntegrationBlueprintData(
        client=client,
        coordinator=coordinator,
        integration=integration,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: IntegrationBlueprintConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
