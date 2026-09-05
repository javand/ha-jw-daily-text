# <img src="https://raw.githubusercontent.com/javand/ha-jw-daily-text/main/custom_components/ha_jw_daily_text/brand/icon.png" width="48" height="48" align="center" alt="JW Daily Text Icon"> JW Daily Text for Home Assistant

[![GitHub Release](https://img.shields.io/github/release/javand/ha-jw-daily-text.svg?style=popout-square)](https://github.com/javand/ha-jw-daily-text/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=popout-square)](https://github.com/hacs/integration)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=javand&repository=ha-jw-daily-text&category=integration)

A Home Assistant custom integration that fetches the daily scripture text and commentary from the Watchtower Online Library (WOL). It exposes dedicated sensor entities for **Today**, **Yesterday**, and **Tomorrow**, specially designed for voice automations (Text-to-Speech) and Home Assistant dashboards.

---

## Features

- 📖 **6 Dedicated Sensor Entities**: Separate sensors for scripture text and commentary for **Today**, **Yesterday**, and **Tomorrow**.
- 🔊 **Text-to-Speech (TTS) Ready**: Full, untruncated scripture and commentary text stored in entity attributes (`text`) to bypass Home Assistant's 255-character state limit.
- ⏰ **Local Midnight Refresh**: Automatically updates at local midnight (in your Home Assistant system timezone) with automatic network retry backoff.
- 🗣️ **Bible Abbreviation Expansion**: Automatically expands abbreviated Bible citations (e.g. `Prov. 3:32` $\rightarrow$ `Proverbs 3:32`, `1 Cor. 13:4` $\rightarrow$ `1 Corinthians 13:4`) for natural TTS pronunciation.
- 🌍 **Multi-Language Support**: Configurable WOL locale (English, Spanish, French, German, Portuguese, etc.).

---

## Entities & Attributes

The integration creates the following 6 sensor entities:

| Entity ID | Name | Description |
| :--- | :--- | :--- |
| `sensor.jw_daily_text_today` | JW Daily Text Today | Today's scripture text |
| `sensor.jw_daily_text_today_comment` | JW Daily Text Today Comment | Today's commentary |
| `sensor.jw_daily_text_yesterday` | JW Daily Text Yesterday | Yesterday's scripture text |
| `sensor.jw_daily_text_yesterday_comment` | JW Daily Text Yesterday Comment | Yesterday's commentary |
| `sensor.jw_daily_text_tomorrow` | JW Daily Text Tomorrow | Tomorrow's scripture text |
| `sensor.jw_daily_text_tomorrow_comment` | JW Daily Text Tomorrow Comment | Tomorrow's commentary |

### Entity Attributes

To comply with Home Assistant's 255-character state limit, the entity `state` is truncated with `…` if long. The **full untruncated text** for TTS is available in `extra_state_attributes`:

#### Scripture Sensors (`today`, `yesterday`, `tomorrow`)
* **`state`**: Scripture text (truncated to 255 chars for UI display).
* **`text`**: Full untruncated scripture verse text (for TTS).
* **`scripture`**: Expanded Bible citation (e.g. `"Proverbs 3:32"`).
* **`day_and_date`**: Formatted date header (e.g. `"Friday, September 4"`).
* **`date`**: ISO date (`YYYY-MM-DD`).

#### Comment Sensors (`today_comment`, `yesterday_comment`, `tomorrow_comment`)
* **`state`**: Commentary text (truncated to 255 chars for UI display).
* **`text`**: Full untruncated commentary text (for TTS).
* **`day_and_date`**: Formatted date header (e.g. `"Friday, September 4"`).
* **`date`**: ISO date (`YYYY-MM-DD`).

---

## Installation

### Method 1: HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=javand&repository=ha-jw-daily-text&category=integration)

1. Click the **Open your Home Assistant instance** badge above or open **HACS** manually in Home Assistant.
2. Click the three dots in the top-right corner and select **Custom repositories**.
3. Add repository URL: `https://github.com/javand/ha-jw-daily-text` with Category **Integration**.
4. Click **Download**.
5. Restart Home Assistant.

### Method 2: Manual Installation

1. Download the latest release `.zip` or clone this repository.
2. Copy the `custom_components/ha_jw_daily_text` folder into your Home Assistant `<config>/custom_components/` directory.
3. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, navigate to **Settings** $\rightarrow$ **Devices & Services**.
2. Click **Add Integration**.
3. Search for **JW Daily Text**.
4. Select your preferred WOL language (default: `English`) and submit.

To change the language at any time, click **Configure** on the integration card.

---

## Automation Example (Text-to-Speech)

Here is an example Home Assistant automation that reads the daily text aloud every morning:

```yaml
alias: Read JW Daily Text Morning
trigger:
  - trigger: time
    at: "08:00:00"
action:
  - action: tts.speak
    target:
      entity_id: tts.google_en_com
    data:
      media_player_entity_id: media_player.living_room_speaker
      message: >
        Daily Text for {{ state_attr('sensor.jw_daily_text_today', 'day_and_date') }}.
        {{ state_attr('sensor.jw_daily_text_today', 'text') }}
        {{ state_attr('sensor.jw_daily_text_today', 'scripture') }}.

        Commentary:
        {{ state_attr('sensor.jw_daily_text_today_comment', 'text') }}
```
