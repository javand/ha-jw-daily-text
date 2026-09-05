# Specification: JW Daily Text Home Assistant Custom Component

## Overview
`ha_jw_daily_text` is a Home Assistant custom integration that fetches the daily scripture text and commentary from Watchtower Online Library (WOL). It exposes separate sensor entities for **Today**, **Yesterday**, and **Tomorrow**, allowing Home Assistant automations to trigger voice readouts (Text-to-Speech) or display daily text information on dashboards.

---

## Architecture & Components

```
┌────────────────────────────────────────────────────────┐
│              JW Daily Text Integration                 │
│                                                        │
│  ┌───────────────────┐        ┌─────────────────────┐  │
│  │   Config Flow     │───────>│  JWTextApiClient    │  │
│  │ (Language Config) │        │ (WOL HTML Parser)   │  │
│  └───────────────────┘        └──────────┬──────────┘  │
│                                          │             │
│                                          ▼             │
│                               ┌─────────────────────┐  │
│                               │ JWDailyText         │  │
│                               │ Coordinator         │  │
│                               │ (Midnight Refresh   │  │
│                               │  + Retry Backoff)   │  │
│                               └──────────┬──────────┘  │
│                                          │             │
│                  ┌───────────────────────┴──────────┐  │
│                  ▼                                  ▼  │
│      ┌───────────────────────┐          ┌───────────────────────┐
│      │   Scripture Sensors   │          │    Comment Sensors    │
│      │ - today               │          │ - today_comment       │
│      │ - yesterday           │          │ - yesterday_comment   │
│      │ - tomorrow            │          │ - tomorrow_comment    │
│      └───────────────────────┘          └───────────────────────┘
└────────────────────────────────────────────────────────┘
```

---

## 1. Integration Domain & Config Flow (`const.py`, `config_flow.py`)

- **Domain**: `ha_jw_daily_text`
- **Integration Title**: `JW Daily Text`
- **Config Flow**:
  - User setup flow requiring no credentials.
  - **Language Selector**: Configurable WOL language / locale code (default: `lp-e` for English). Supports common locales such as `lp-s` (Spanish), `lp-f` (French), `lp-po` (Portuguese), `lp-x` (German), etc.
- **Options Flow**:
  - Allows changing the configured language dynamically post-installation without re-adding the integration.

---

## 2. Data Fetching & HTML Parsing (`api.py`)

### WOL URL Format
Direct date URL pattern:
`https://wol.jw.org/{lang}/wol/dt/r1/{locale_code}/{YYYY}/{MM}/{DD}`

### Parsing & Extraction Logic
1. **`day_and_date`**: Extracted from header/date text (e.g. `"Friday, September 4"`).
2. **`scripture_text`**: Extracted from primary verse block (`<p class="themeScrp">`). Strips HTML markup, superscripts, and footnote links.
3. **`scripture`**: Extracted from verse citation following dash (`—` or `-`).
   - Abbreviated book names are expanded to full proper names using a built-in Bible book dictionary (e.g. `Prov. 3:32` $\rightarrow$ `"Proverbs 3:32"`, `Gen. 18:25` $\rightarrow$ `"Genesis 18:25"`, `1 Cor. 13:4` $\rightarrow$ `"1 Corinthians 13:4"`).
4. **`comments`**: Extracted from commentary block (`<div class="bodyTxt">`). Normalizes whitespace and strips trailing publication references.

### Data Model
```python
@dataclass
class DailyTextEntry:
    date: str  # YYYY-MM-DD
    day_and_date: str  # e.g. "Friday, September 4"
    scripture_text: str  # e.g. "Jehovah detests a devious person..."
    scripture: str  # e.g. "Proverbs 3:32" (fully expanded)
    comments: str  # e.g. "We can learn about the importance..."


@dataclass
class JWDailyTextData:
    yesterday: DailyTextEntry
    today: DailyTextEntry
    tomorrow: DailyTextEntry
```

---

## 3. Data Coordinator & Midnight Refresh (`coordinator.py`)

- **Class**: `JWDailyTextCoordinator(DataUpdateCoordinator)`
- **Scheduling**:
  - Calculates local midnight in Home Assistant's configured system timezone:
    `next_midnight = dt_util.start_of_local_day(now + timedelta(days=1)) + timedelta(seconds=5)`
  - Schedules updates using `async_track_point_in_time`.
- **Edge Case Resilience**:
  - **Initial Setup / Offline Boot**: If internet is down on initial boot, raises `ConfigEntryNotReady` so Home Assistant automatically retries.
  - **Midnight Outage / Network Errors**: Retains cached data (entities remain available) and retries with exponential backoff (1 min $\rightarrow$ 5 min $\rightarrow$ 15 min $\rightarrow$ 30 min) until successful, then re-aligns to next local midnight.

---

## 4. Sensor Entities & Attribute Schema (`sensor.py`)

### Registered Entities

1. `sensor.jw_daily_text_today`
2. `sensor.jw_daily_text_today_comment`
3. `sensor.jw_daily_text_yesterday`
4. `sensor.jw_daily_text_yesterday_comment`
5. `sensor.jw_daily_text_tomorrow`
6. `sensor.jw_daily_text_tomorrow_comment`

### State & Attribute Mapping

#### Scripture Sensors (`today`, `yesterday`, `tomorrow`)
- **`state`**: `scripture_text` truncated to 255 characters (with `…` if longer).
- **`extra_state_attributes`**:
  - `text`: `scripture_text` (full untruncated string for TTS)
  - `scripture`: `scripture` (expanded citation, e.g. `"Proverbs 3:32"`)
  - `day_and_date`: `day_and_date` (e.g. `"Friday, September 4"`)
  - `date`: `YYYY-MM-DD`

#### Comment Sensors (`today_comment`, `yesterday_comment`, `tomorrow_comment`)
- **`state`**: `comments` truncated to 255 characters (with `…` for UI).
- **`extra_state_attributes`**:
  - `text`: `comments` (full untruncated commentary text for TTS)
  - `day_and_date`: `day_and_date` (e.g. `"Friday, September 4"`)
  - `date`: `YYYY-MM-DD`

---

## 5. Testing & Verification Plan

1. **Unit Tests**:
   - `test_api.py`: Tests HTML parsing, edge cases, missing elements, Bible book abbreviation expansion, and network error handling.
   - `test_coordinator.py`: Tests initial refresh, midnight calculation, and retry backoff.
   - `test_sensor.py`: Verifies state truncation, attributes, and 6 registered sensor entities.
2. **Quality Checks**:
   - Run `ruff check . --fix` and `ruff format .`.
   - Run `pytest` / Home Assistant test harness.
