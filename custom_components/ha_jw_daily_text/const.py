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
ATTRIBUTION = "Data provided by Watchtower Online Library"
