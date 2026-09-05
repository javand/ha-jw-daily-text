# JW Daily Text Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Home Assistant custom component (`ha_jw_daily_text`) that fetches the daily scripture text and commentary from Watchtower Online Library (WOL) for Today, Yesterday, and Tomorrow, and exposes 6 sensor entities configured for TTS voice automations and dashboard presentation.

**Architecture:** A `JWTextApiClient` fetches and parses daily text HTML from WOL, handling Bible book abbreviation expansion and HTML cleanup into structured `DailyTextEntry` dataclasses. A `JWDailyTextCoordinator` coordinates updates scheduled for local midnight using `async_track_point_in_time` with exponential backoff retries on network failures. Six `sensor` entities expose state (truncated to 255 characters) and full untruncated text in attributes for TTS automations.

**Tech Stack:** Python 3.12+, Home Assistant Core (`homeassistant`), `aiohttp`, `beautifulsoup4` (or built-in `html.parser`), `pytest`, `pytest-homeassistant-custom-component`.

**Spec:** [docs/superpowers/specs/2026-09-04-jw-daily-text-design.md](file:///Users/javan/Projects/ha-jw-daily-text/docs/superpowers/specs/2026-09-04-jw-daily-text-design.md)

## Global Constraints

- Domain name: `ha_jw_daily_text`
- Integration Title: `JW Daily Text`
- State limit constraint: Max 255 characters in entity `state`; complete full text stored in `extra_state_attributes["text"]`
- Update schedule: Local midnight (system timezone) + 5 seconds buffer

---

### Task 1: Constants & Manifest Configuration

**Files:**
- Modify: `custom_components/ha_jw_daily_text/const.py`
- Modify: `custom_components/ha_jw_daily_text/manifest.json`
- Create: `tests/test_const.py`

**Interfaces:**
- Produces: `DOMAIN = "ha_jw_daily_text"`, `DEFAULT_LANGUAGE = "lp-e"`, `SUPPORTED_LANGUAGES = {"English": "lp-e", "Spanish": "lp-s", "French": "lp-f", "German": "lp-x", "Portuguese": "lp-po"}`

- [ ] **Step 1: Write failing test for constants and manifest**

```python
# tests/test_const.py
from custom_components.ha_jw_daily_text.const import (
    DEFAULT_LANGUAGE,
    DOMAIN,
    SUPPORTED_LANGUAGES,
)


def test_constants():
    assert DOMAIN == "ha_jw_daily_text"
    assert DEFAULT_LANGUAGE == "lp-e"
    assert "English" in SUPPORTED_LANGUAGES
    assert SUPPORTED_LANGUAGES["English"] == "lp-e"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_const.py -v`
Expected: FAIL (constants not updated yet)

- [ ] **Step 3: Update `const.py` and `manifest.json`**

Update `custom_components/ha_jw_daily_text/const.py`:
```python
"""Constants for ha_jw_daily_text."""

import logging

DOMAIN = "ha_jw_daily_text"
LOGGER = logging.getLogger(__package__)

DEFAULT_LANGUAGE = "lp-e"
SUPPORTED_LANGUAGES = {
    "English": "lp-e",
    "Spanish": "lp-s",
    "French": "lp-f",
    "German": "lp-x",
    "Portuguese": "lp-po",
}
```

Update `custom_components/ha_jw_daily_text/manifest.json`:
```json
{
  "domain": "ha_jw_daily_text",
  "name": "JW Daily Text",
  "codeowners": [
    "@ludeeus"
  ],
  "config_flow": true,
  "documentation": "https://github.com/ludeeus/integration_blueprint",
  "iot_class": "cloud_polling",
  "issue_tracker": "https://github.com/ludeeus/integration_blueprint/issues",
  "version": "0.1.0"
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_const.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/ha_jw_daily_text/const.py custom_components/ha_jw_daily_text/manifest.json tests/test_const.py
git commit -m "feat: setup domain constants and manifest for ha_jw_daily_text"
```

---

### Task 2: API Client & Bible Abbreviation Expansion (`api.py`)

**Files:**
- Create/Modify: `custom_components/ha_jw_daily_text/api.py`
- Create: `tests/test_api.py`

**Interfaces:**
- Consumes: `DEFAULT_LANGUAGE` from `const.py`
- Produces: `DailyTextEntry` dataclass, `JWTextApiClient` class with `async_get_entry_for_date(date: datetime.date)` and `async_get_daily_text_data(target_date: datetime.date)` returning `JWDailyTextData`.

- [ ] **Step 1: Write failing tests for HTML parsing and Bible book expansion**

```python
# tests/test_api.py
import datetime
from unittest.mock import AsyncMock, patch

import pytest
from custom_components.ha_jw_daily_text.api import JWTextApiClient, expand_bible_citation


def test_expand_bible_citation():
    assert expand_bible_citation("Prov. 3:32") == "Proverbs 3:32"
    assert expand_bible_citation("Gen. 18:25") == "Genesis 18:25"
    assert expand_bible_citation("1 Cor. 13:4") == "1 Corinthians 13:4"
    assert expand_bible_citation("Ps. 23:1") == "Psalms 23:1"


@pytest.mark.asyncio
async def test_api_client_parse():
    sample_html = """
    <article>
        <h2>Friday, September 4</h2>
        <p class="themeScrp">Jehovah detests a devious person, but His close friendship is with the upright.​—Prov. 3:32.</p>
        <div class="bodyTxt"><p>We can learn about the importance of having a sincere heart from Jesus.</p></div>
    </article>
    """
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = sample_html
    mock_session.request.return_value.__aenter__.return_value = mock_response

    client = JWTextApiClient(session=mock_session, language="lp-e")
    entry = await client.async_get_entry_for_date(datetime.date(2026, 9, 4))

    assert entry.date == "2026-09-04"
    assert entry.day_and_date == "Friday, September 4"
    assert entry.scripture_text == "Jehovah detests a devious person, but His close friendship is with the upright."
    assert entry.scripture == "Proverbs 3:32"
    assert entry.comments == "We can learn about the importance of having a sincere heart from Jesus."
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py -v`
Expected: FAIL (`JWTextApiClient` or `expand_bible_citation` not defined)

- [ ] **Step 3: Implement `api.py`**

Create/Modify `custom_components/ha_jw_daily_text/api.py`:
```python
"""API client for JW Daily Text from WOL."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import datetime
from html.parser import HTMLParser
import re

import aiohttp

BIBLE_BOOKS = {
    "Gen.": "Genesis",
    "Gen": "Genesis",
    "Ex.": "Exodus",
    "Ex": "Exodus",
    "Lev.": "Leviticus",
    "Lev": "Leviticus",
    "Num.": "Numbers",
    "Num": "Numbers",
    "Deut.": "Deuteronomy",
    "Deut": "Deuteronomy",
    "Josh.": "Joshua",
    "Josh": "Joshua",
    "Judg.": "Judges",
    "Judg": "Judges",
    "Ruth": "Ruth",
    "1 Sam.": "1 Samuel",
    "2 Sam.": "2 Samuel",
    "1 Kings": "1 Kings",
    "2 Kings": "2 Kings",
    "1 Chron.": "1 Chronicles",
    "2 Chron.": "2 Chronicles",
    "Ezra": "Ezra",
    "Neh.": "Nehemiah",
    "Esth.": "Esther",
    "Job": "Job",
    "Ps.": "Psalms",
    "Pss.": "Psalms",
    "Prov.": "Proverbs",
    "Prov": "Proverbs",
    "Eccl.": "Ecclesiastes",
    "Song of Sol.": "Song of Solomon",
    "Isa.": "Isaiah",
    "Isa": "Isaiah",
    "Jer.": "Jeremiah",
    "Jer": "Jeremiah",
    "Lam.": "Lamentations",
    "Ezek.": "Ezekiel",
    "Dan.": "Daniel",
    "Hos.": "Hosea",
    "Joel": "Joel",
    "Amos": "Amos",
    "Obad.": "Obadiah",
    "Jonah": "Jonah",
    "Mic.": "Micah",
    "Nah.": "Nahum",
    "Hab.": "Habakkuk",
    "Zeph.": "Zephaniah",
    "Hag.": "Haggai",
    "Zech.": "Zechariah",
    "Mal.": "Malachi",
    "Matt.": "Matthew",
    "Matt": "Matthew",
    "Mark": "Mark",
    "Luke": "Luke",
    "John": "John",
    "Acts": "Acts",
    "Rom.": "Romans",
    "Rom": "Romans",
    "1 Cor.": "1 Corinthians",
    "2 Cor.": "2 Corinthians",
    "Gal.": "Galatians",
    "Eph.": "Ephesians",
    "Phil.": "Philippians",
    "Col.": "Colossians",
    "1 Thess.": "1 Thessalonians",
    "2 Thess.": "2 Thessalonians",
    "1 Tim.": "1 Timothy",
    "2 Tim.": "2 Timothy",
    "Titus": "Titus",
    "Philem.": "Philemon",
    "Heb.": "Hebrews",
    "Jas.": "James",
    "Jas": "James",
    "1 Pet.": "1 Peter",
    "2 Pet.": "2 Peter",
    "1 John": "1 John",
    "2 John": "2 John",
    "3 John": "3 John",
    "Jude": "Jude",
    "Rev.": "Revelation",
}


def expand_bible_citation(citation: str) -> str:
    """Expand abbreviated Bible book name to full proper name."""
    clean_citation = citation.strip().rstrip(".")
    for abbr, full_name in sorted(
        BIBLE_BOOKS.items(), key=lambda x: len(x[0]), reverse=True
    ):
        if clean_citation.startswith(abbr):
            remainder = clean_citation[len(abbr) :].strip()
            return f"{full_name} {remainder}".strip()
    return clean_citation


class HTMLStripper(HTMLParser):
    """Simple HTML text stripper."""

    def __init__(self) -> None:
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text: list[str] = []

    def handle_data(self, d: str) -> None:
        self.text.append(d)

    def get_data(self) -> str:
        return "".join(self.text)


def strip_html(html_str: str) -> str:
    """Strip HTML tags from string."""
    stripper = HTMLStripper()
    stripper.feed(html_str)
    return stripper.get_data().strip()


@dataclass
class DailyTextEntry:
    """Data class for single date daily text."""

    date: str
    day_and_date: str
    scripture_text: str
    scripture: str
    comments: str


@dataclass
class JWDailyTextData:
    """Container for yesterday, today, and tomorrow daily text data."""

    yesterday: DailyTextEntry
    today: DailyTextEntry
    tomorrow: DailyTextEntry


class JWTextApiClientError(Exception):
    """General API client error."""


class JWTextApiClientCommunicationError(JWTextApiClientError):
    """Communication error."""


class JWTextApiClient:
    """API client for WOL Daily Text."""

    def __init__(
        self, session: aiohttp.ClientSession, language: str = "lp-e"
    ) -> None:
        self._session = session
        self._language = language

    async def async_get_entry_for_date(
        self, date_val: datetime.date
    ) -> DailyTextEntry:
        """Fetch and parse daily text for a given date."""
        lang_prefix = "en"
        if self._language == "lp-s":
            lang_prefix = "es"
        elif self._language == "lp-f":
            lang_prefix = "fr"
        elif self._language == "lp-x":
            lang_prefix = "de"

        url = f"https://wol.jw.org/{lang_prefix}/wol/dt/r1/{self._language}/{date_val.year}/{date_val.month:02d}/{date_val.day:02d}"

        try:
            async with asyncio.timeout(10):
                response = await self._session.request(method="GET", url=url)
                if response.status != 200:
                    raise JWTextApiClientCommunicationError(
                        f"HTTP {response.status} fetching daily text"
                    )
                html = await response.text()
        except Exception as err:
            raise JWTextApiClientCommunicationError(
                f"Error fetching WOL: {err}"
            ) from err

        return self._parse_html(date_val.strftime("%Y-%m-%d"), html)

    def _parse_html(self, date_str: str, html: str) -> DailyTextEntry:
        """Parse WOL HTML into DailyTextEntry."""
        # Find day header (<h2>)
        h2_match = re.search(r"<h2.*?>(.*?)</h2>", html, re.DOTALL)
        day_and_date = (
            strip_html(h2_match.group(1)) if h2_match else "Daily Text"
        )

        # Find theme scripture paragraph
        scripture_text = ""
        scripture_citation = ""
        theme_match = re.search(
            r'<p class="themeScrp">(.*?)</p>', html, re.DOTALL
        )
        if theme_match:
            raw_theme = strip_html(theme_match.group(1))
            # Split by em-dash or dash
            parts = re.split(r"—|-", raw_theme, maxsplit=1)
            scripture_text = parts[0].strip()
            if len(parts) > 1:
                raw_citation = parts[1].strip()
                scripture_citation = expand_bible_citation(raw_citation)
            else:
                scripture_citation = ""

        # Find commentary body
        comments = ""
        body_match = re.search(
            r'<div class="bodyTxt">(.*?)</div>\s*</div>', html, re.DOTALL
        )
        if body_match:
            raw_body = strip_html(body_match.group(1))
            # Strip trailing publication reference (e.g. w24.06 10 ¶7)
            comments = re.sub(r"\s*w\d{2}\.\d{2}.*$", "", raw_body).strip()

        return DailyTextEntry(
            date=date_str,
            day_and_date=day_and_date,
            scripture_text=scripture_text,
            scripture=scripture_citation,
            comments=comments,
        )

    async def async_get_daily_text_data(
        self, today_date: datetime.date
    ) -> JWDailyTextData:
        """Fetch yesterday, today, and tomorrow in parallel."""
        yesterday_date = today_date - datetime.timedelta(days=1)
        tomorrow_date = today_date + datetime.timedelta(days=1)

        yesterday, today, tomorrow = await asyncio.gather(
            self.async_get_entry_for_date(yesterday_date),
            self.async_get_entry_for_date(today_date),
            self.async_get_entry_for_date(tomorrow_date),
        )

        return JWDailyTextData(
            yesterday=yesterday, today=today, tomorrow=tomorrow
        )
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/ha_jw_daily_text/api.py tests/test_api.py
git commit -m "feat: implement JWTextApiClient and Bible book citation expansion"
```

---

### Task 3: DataUpdateCoordinator & Midnight Schedule (`coordinator.py`)

**Files:**
- Create/Modify: `custom_components/ha_jw_daily_text/coordinator.py`
- Create: `tests/test_coordinator.py`

**Interfaces:**
- Consumes: `JWTextApiClient`, `JWDailyTextData` from `api.py`
- Produces: `JWDailyTextCoordinator` inheriting from `DataUpdateCoordinator`. Exposes `async_setup_midnight_schedule()`.

- [ ] **Step 1: Write failing test for coordinator and midnight calculations**

```python
# tests/test_coordinator.py
import datetime
from unittest.mock import AsyncMock, patch

import pytest
from custom_components/ha_jw_daily_text.api import DailyTextEntry, JWDailyTextData
from custom_components/ha_jw_daily_text.coordinator import JWDailyTextCoordinator
from homeassistant.util import dt as dt_util


@pytest.mark.asyncio
async def test_coordinator_update(hass):
    mock_api = AsyncMock()
    mock_data = JWDailyTextData(
        yesterday=DailyTextEntry("2026-09-03", "Thursday, Sep 3", "Text Y", "Gen 1:1", "Comment Y"),
        today=DailyTextEntry("2026-09-04", "Friday, Sep 4", "Text T", "Prov 3:32", "Comment T"),
        tomorrow=DailyTextEntry("2026-09-05", "Saturday, Sep 5", "Text Tm", "Rev 1:1", "Comment Tm"),
    )
    mock_api.async_get_daily_text_data.return_value = mock_data

    coordinator = JWDailyTextCoordinator(hass, mock_api)
    data = await coordinator._async_update_data()

    assert data.today.date == "2026-09-04"
    assert data.today.scripture == "Prov 3:32"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_coordinator.py -v`
Expected: FAIL (`JWDailyTextCoordinator` not defined)

- [ ] **Step 3: Implement `coordinator.py`**

Create/Modify `custom_components/ha_jw_daily_text/coordinator.py`:
```python
"""DataUpdateCoordinator for ha_jw_daily_text."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .api import (
    JWTextApiClient,
    JWTextApiClientCommunicationError,
    JWDailyTextData,
)
from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class JWDailyTextCoordinator(DataUpdateCoordinator[JWDailyTextData]):
    """Class to manage fetching JW Daily Text data."""

    def __init__(self, hass: HomeAssistant, api_client: JWTextApiClient) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
        )
        self.api_client = api_client
        self._unsub_midnight_timer = None
        self._retry_count = 0

    async def _async_update_data(self) -> JWDailyTextData:
        """Fetch data from WOL."""
        now = dt_util.now()
        today_date = now.date()

        try:
            data = await self.api_client.async_get_daily_text_data(today_date)
            self._retry_count = 0
            self._schedule_next_midnight()
            return data
        except JWTextApiClientCommunicationError as err:
            self._retry_count += 1
            backoff_minutes = min(2 ** self._retry_count, 30)
            LOGGER.warning(
                "Error fetching JW Daily Text (%s). Retrying in %d minutes.",
                err,
                backoff_minutes,
            )
            # Schedule retry
            retry_time = dt_util.now() + timedelta(minutes=backoff_minutes)
            async_track_point_in_time(
                self.hass, self._async_scheduled_update, retry_time
            )
            if self.data is not None:
                # Keep existing data on failure
                return self.data
            raise UpdateFailed(err) from err

    def _schedule_next_midnight(self) -> None:
        """Schedule next update at local midnight."""
        if self._unsub_midnight_timer is not None:
            self._unsub_midnight_timer()

        now = dt_util.now()
        tomorrow_start = dt_util.start_of_local_day(now + timedelta(days=1))
        # Add 5 seconds buffer
        next_midnight = tomorrow_start + timedelta(seconds=5)

        self._unsub_midnight_timer = async_track_point_in_time(
            self.hass, self._async_scheduled_update, next_midnight
        )

    async def _async_scheduled_update(self, now: datetime) -> None:
        """Handle scheduled update timer."""
        await self.async_refresh()
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_coordinator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/ha_jw_daily_text/coordinator.py tests/test_coordinator.py
git commit -m "feat: implement JWDailyTextCoordinator with local midnight scheduling and retry backoff"
```

---

### Task 4: Config Flow & Options Flow (`config_flow.py`, `en.json`)

**Files:**
- Create/Modify: `custom_components/ha_jw_daily_text/config_flow.py`
- Modify: `custom_components/ha_jw_daily_text/translations/en.json`
- Create: `tests/test_config_flow.py`

**Interfaces:**
- Consumes: `SUPPORTED_LANGUAGES`, `DEFAULT_LANGUAGE` from `const.py`
- Produces: `JWTextConfigFlow` and `JWTextOptionsFlowHandler`

- [ ] **Step 1: Write failing test for config flow**

```python
# tests/test_config_flow.py
from unittest.mock import patch
import pytest
from custom_components.ha_jw_daily_text.const import DOMAIN
from homeassistant import config_entries, data_entry_flow


@pytest.mark.asyncio
async def test_flow_user(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"language": "lp-e"},
    )
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "JW Daily Text"
    assert result2["data"]["language"] == "lp-e"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config_flow.py -v`
Expected: FAIL (`config_flow` not updated)

- [ ] **Step 3: Update `config_flow.py` and `translations/en.json`**

Update `custom_components/ha_jw_daily_text/config_flow.py`:
```python
"""Config flow for ha_jw_daily_text."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_LANGUAGE, DOMAIN, SUPPORTED_LANGUAGES


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
                vol.Required(
                    "language", default=DEFAULT_LANGUAGE
                ): vol.In(SUPPORTED_LANGUAGES)
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
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_lang = self.config_entry.options.get(
            "language",
            self.config_entry.data.get("language", DEFAULT_LANGUAGE),
        )

        schema = vol.Schema(
            {
                vol.Required("language", default=current_lang): vol.In(
                    SUPPORTED_LANGUAGES
                )
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
```

Update `custom_components/ha_jw_daily_text/translations/en.json`:
```json
{
    "config": {
        "step": {
            "user": {
                "title": "JW Daily Text",
                "description": "Configure JW Daily Text integration settings.",
                "data": {
                    "language": "WOL Language"
                }
            }
        },
        "abort": {
            "already_configured": "JW Daily Text is already configured."
        }
    },
    "options": {
        "step": {
            "init": {
                "title": "JW Daily Text Options",
                "data": {
                    "language": "WOL Language"
                }
            }
        }
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config_flow.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/ha_jw_daily_text/config_flow.py custom_components/ha_jw_daily_text/translations/en.json tests/test_config_flow.py
git commit -m "feat: implement config flow and options flow for language selection"
```

---

### Task 5: Sensor Entities & Entry Setup (`sensor.py`, `__init__.py`)

**Files:**
- Create/Modify: `custom_components/ha_jw_daily_text/sensor.py`
- Modify: `custom_components/ha_jw_daily_text/__init__.py`
- Create: `tests/test_sensor.py`

**Interfaces:**
- Consumes: `JWDailyTextCoordinator` from `coordinator.py`
- Produces: 6 `JWDailyTextSensor` entities (`today`, `today_comment`, `yesterday`, `yesterday_comment`, `tomorrow`, `tomorrow_comment`) registered in Home Assistant.

- [ ] **Step 1: Write failing test for sensor entities**

```python
# tests/test_sensor.py
import pytest
from unittest.mock import AsyncMock
from custom_components.ha_jw_daily_text.api import DailyTextEntry, JWDailyTextData
from custom_components.ha_jw_daily_text.coordinator import JWDailyTextCoordinator
from custom_components.ha_jw_daily_text.sensor import JWDailyTextSensor


def test_sensor_state_truncation_and_attributes(hass):
    long_text = "A" * 300
    entry = DailyTextEntry(
        date="2026-09-04",
        day_and_date="Friday, September 4",
        scripture_text=long_text,
        scripture="Proverbs 3:32",
        comments="Short comment",
    )
    mock_data = JWDailyTextData(yesterday=entry, today=entry, tomorrow=entry)
    coordinator = AsyncMock()
    coordinator.data = mock_data

    sensor = JWDailyTextSensor(
        coordinator=coordinator,
        target_day="today",
        field_type="text",
        name="JW Daily Text Today",
        unique_id="jw_daily_text_today",
    )

    # State truncated to 255 chars
    assert len(sensor.native_value) == 255
    assert sensor.native_value.endswith("…")

    # Extra state attributes contain full untruncated text
    attrs = sensor.extra_state_attributes
    assert attrs["text"] == long_text
    assert attrs["scripture"] == "Proverbs 3:32"
    assert attrs["day_and_date"] == "Friday, September 4"
    assert attrs["date"] == "2026-09-04"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_sensor.py -v`
Expected: FAIL (`JWDailyTextSensor` not defined)

- [ ] **Step 3: Implement `sensor.py` and `__init__.py`**

Create/Modify `custom_components/ha_jw_daily_text/sensor.py`:
```python
"""Sensor platform for ha_jw_daily_text."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import JWDailyTextCoordinator
from .data import IntegrationBlueprintData


def truncate_state(value: str, max_len: int = 255) -> str:
    """Truncate string to max length for HA state."""
    if len(value) <= max_len:
        return value
    return value[: max_len - 1] + "…"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    data_obj: IntegrationBlueprintData = entry.runtime_data
    coordinator: JWDailyTextCoordinator = data_obj.coordinator

    sensors = [
        JWDailyTextSensor(
            coordinator, "today", "text", "JW Daily Text Today", "jw_daily_text_today"
        ),
        JWDailyTextSensor(
            coordinator,
            "today",
            "comment",
            "JW Daily Text Today Comment",
            "jw_daily_text_today_comment",
        ),
        JWDailyTextSensor(
            coordinator,
            "yesterday",
            "text",
            "JW Daily Text Yesterday",
            "jw_daily_text_yesterday",
        ),
        JWDailyTextSensor(
            coordinator,
            "yesterday",
            "comment",
            "JW Daily Text Yesterday Comment",
            "jw_daily_text_yesterday_comment",
        ),
        JWDailyTextSensor(
            coordinator,
            "tomorrow",
            "text",
            "JW Daily Text Tomorrow",
            "jw_daily_text_tomorrow",
        ),
        JWDailyTextSensor(
            coordinator,
            "tomorrow",
            "comment",
            "JW Daily Text Tomorrow Comment",
            "jw_daily_text_tomorrow_comment",
        ),
    ]

    async_add_entities(sensors)


class JWDailyTextSensor(CoordinatorEntity[JWDailyTextCoordinator], SensorEntity):
    """Representation of a JW Daily Text sensor."""

    def __init__(
        self,
        coordinator: JWDailyTextCoordinator,
        target_day: str,
        field_type: str,
        name: str,
        unique_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._target_day = target_day
        self._field_type = field_type
        self._attr_name = name
        self._attr_unique_id = unique_id

    @property
    def _entry_data(self):
        if self.coordinator.data is None:
            return None
        return getattr(self.coordinator.data, self._target_day, None)

    @property
    def native_value(self) -> str | None:
        """Return state truncated to 255 chars."""
        entry = self._entry_data
        if entry is None:
            return None
        val = (
            entry.scripture_text if self._field_type == "text" else entry.comments
        )
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
```

Update `custom_components/ha_jw_daily_text/__init__.py`:
```python
"""Custom integration to integrate JW Daily Text with Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import JWTextApiClient
from .const import DEFAULT_LANGUAGE, DOMAIN
from .coordinator import JWDailyTextCoordinator
from .data import IntegrationBlueprintData

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up JW Daily Text from a config entry."""
    lang = entry.options.get("language", entry.data.get("language", DEFAULT_LANGUAGE))
    session = async_get_clientsession(hass)
    api_client = JWTextApiClient(session=session, language=lang)

    coordinator = JWDailyTextCoordinator(hass, api_client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = IntegrationBlueprintData(
        client=api_client,
        integration=None,
        coordinator=coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_sensor.py -v`
Expected: PASS

- [ ] **Step 5: Run full test suite & linter**

Run:
`./scripts/lint`
`pytest`

- [ ] **Step 6: Commit**

```bash
git add custom_components/ha_jw_daily_text/sensor.py custom_components/ha_jw_daily_text/__init__.py tests/test_sensor.py
git commit -m "feat: implement sensor platform with state truncation and TTS attribute model"
```
