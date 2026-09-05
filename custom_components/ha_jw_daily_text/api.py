"""API client for JW Daily Text from WOL."""

from __future__ import annotations

import asyncio
import datetime
import re
import socket
from dataclasses import dataclass
from html.parser import HTMLParser
from http import HTTPStatus

import aiohttp

from .bible_books import expand_bible_citation
from .const import DEFAULT_LANGUAGE

LANGUAGE_PREFIXES: dict[str, str] = {
    "lp-e": "en",
    "lp-s": "es",
    "lp-f": "fr",
    "lp-x": "de",
    "lp-po": "pt",
}

LANGUAGE_CODE_MAP: dict[str, str] = {
    "english": "lp-e",
    "spanish": "lp-s",
    "french": "lp-f",
    "german": "lp-x",
    "portuguese": "lp-po",
    "lp-e": "lp-e",
    "lp-s": "lp-s",
    "lp-f": "lp-f",
    "lp-x": "lp-x",
    "lp-po": "lp-po",
}


class HTMLStripper(HTMLParser):
    """Simple HTML text stripper."""

    def __init__(self) -> None:
        """Initialize the HTML stripper."""
        super().__init__(convert_charrefs=True)
        self.reset()
        self.text: list[str] = []

    def handle_data(self, data: str) -> None:
        """Collect text data."""
        self.text.append(data)

    def handle_endtag(self, tag: str) -> None:
        """Append space on block end tags to prevent word merging."""
        if tag in ("p", "div", "br", "li", "h1", "h2", "h3"):
            self.text.append(" ")

    def get_data(self) -> str:
        """Return gathered text."""
        return "".join(self.text)


def strip_html(html_str: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    stripper = HTMLStripper()
    stripper.feed(html_str)
    raw = stripper.get_data()
    cleaned = raw.replace("\u200b", "").replace("\xa0", " ")
    return re.sub(r"\s+", " ", cleaned).strip()


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


def _verify_response_or_raise(response: aiohttp.ClientResponse, url: str) -> None:
    """Verify HTTP response status or raise communication error."""
    if response.status != HTTPStatus.OK:
        msg = f"HTTP {response.status} fetching daily text from {url}"
        raise JWTextApiClientCommunicationError(msg)


class JWTextApiClient:
    """API client for WOL Daily Text."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        language: str = DEFAULT_LANGUAGE,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        clean_lang = language.lower() if isinstance(language, str) else DEFAULT_LANGUAGE
        self._language = LANGUAGE_CODE_MAP.get(clean_lang, DEFAULT_LANGUAGE)

    async def async_get_entry_for_date(self, date_val: datetime.date) -> DailyTextEntry:
        """Fetch and parse daily text for a given date."""
        lang_prefix = LANGUAGE_PREFIXES.get(self._language, "en")
        url = (
            f"https://wol.jw.org/{lang_prefix}/wol/dt/r1/{self._language}/"
            f"{date_val.year}/{date_val.month:02d}/{date_val.day:02d}"
        )

        try:
            async with asyncio.timeout(10):
                req = self._session.request(method="GET", url=url)
                if hasattr(req, "__aenter__"):
                    async with req as response:
                        _verify_response_or_raise(response, url)
                        html = await response.text()
                else:
                    response = await req
                    _verify_response_or_raise(response, url)
                    html = await response.text()
        except TimeoutError as err:
            msg = f"Timeout fetching daily text from {url}: {err}"
            raise JWTextApiClientCommunicationError(msg) from err
        except (aiohttp.ClientError, socket.gaierror) as err:
            msg = f"Error fetching daily text from {url}: {err}"
            raise JWTextApiClientCommunicationError(msg) from err
        except JWTextApiClientCommunicationError:
            raise
        except Exception as err:
            msg = f"Unexpected error fetching daily text from {url}: {err}"
            raise JWTextApiClientError(msg) from err

        return self._parse_html(date_val.strftime("%Y-%m-%d"), html)

    def _parse_html(self, date_str: str, html: str) -> DailyTextEntry:
        """Parse WOL HTML into DailyTextEntry."""
        # Find day header (<h2>)
        h2_match = re.search(r"<h2[^>]*>(.*?)</h2>", html, re.DOTALL)
        day_and_date = strip_html(h2_match.group(1)) if h2_match else "Daily Text"
        if not day_and_date:
            day_and_date = "Daily Text"

        # Find theme scripture paragraph (<p class="themeScrp">)
        scripture_text = ""
        scripture_citation = ""
        theme_match = re.search(r'<p class="themeScrp"[^>]*>(.*?)</p>', html, re.DOTALL)
        if theme_match:
            raw_theme = strip_html(theme_match.group(1))
            parts: list[str] = []
            for sep in ("—", "\u2013", "--", " - ", ".-"):
                if sep in raw_theme:
                    parts = raw_theme.rsplit(sep, 1)
                    break
            if not parts and "-" in raw_theme:
                parts = raw_theme.rsplit("-", 1)

            if parts:
                scripture_text = parts[0].strip()
                raw_citation = parts[1].strip()
                scripture_citation = expand_bible_citation(raw_citation)
            else:
                scripture_text = raw_theme
                scripture_citation = ""

        # Find commentary body (<div class="bodyTxt">)
        comments = ""
        body_match = re.search(
            r'<div class="bodyTxt"[^>]*>(.*?)</div>', html, re.DOTALL
        )
        if body_match:
            raw_body = strip_html(body_match.group(1))
            # Strip trailing publication reference (e.g. w24.06 10 ¶7)
            comments = re.sub(
                r"\s*w\d{2}(?:\.\d{2})?.*$", "", raw_body, flags=re.DOTALL
            ).strip()

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
            yesterday=yesterday,
            today=today,
            tomorrow=tomorrow,
        )


# Backward compatibility aliases for blueprint template
IntegrationBlueprintApiClient = JWTextApiClient
IntegrationBlueprintApiClientError = JWTextApiClientError
IntegrationBlueprintApiClientCommunicationError = JWTextApiClientCommunicationError
IntegrationBlueprintApiClientAuthenticationError = JWTextApiClientError
IntegrationBlueprintApiClientRateLimitError = JWTextApiClientError
