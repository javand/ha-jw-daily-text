"""Constants for ha_jw_daily_text."""

import logging

DOMAIN = "ha_jw_daily_text"
LOGGER = logging.getLogger(__package__)

DEFAULT_LANGUAGE = "lp-e"
SUPPORTED_LANGUAGES = {
    "lp-e": "English",
    "lp-s": "Spanish",
    "lp-f": "French",
    "lp-x": "German",
    "lp-po": "Portuguese",
}
ATTRIBUTION = "Data provided by Watchtower Online Library"
