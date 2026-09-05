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

from .const import DEFAULT_LANGUAGE

LANGUAGE_PREFIXES: dict[str, str] = {
    "lp-e": "en",
    "lp-s": "es",
    "lp-f": "fr",
    "lp-x": "de",
    "lp-po": "pt",
}

BIBLE_BOOKS: dict[str, str] = {
    # Genesis
    "Gen.": "Genesis",
    "Gen": "Genesis",
    "Genesis": "Genesis",
    # Exodus
    "Ex.": "Exodus",
    "Ex": "Exodus",
    "Exod.": "Exodus",
    "Exodus": "Exodus",
    # Leviticus
    "Lev.": "Leviticus",
    "Lev": "Leviticus",
    "Leviticus": "Leviticus",
    # Numbers
    "Num.": "Numbers",
    "Num": "Numbers",
    "Numbers": "Numbers",
    # Deuteronomy
    "Deut.": "Deuteronomy",
    "Deut": "Deuteronomy",
    "Deuteronomy": "Deuteronomy",
    # Joshua
    "Josh.": "Joshua",
    "Josh": "Joshua",
    "Joshua": "Joshua",
    # Judges
    "Judg.": "Judges",
    "Judg": "Judges",
    "Judges": "Judges",
    # Ruth
    "Ruth": "Ruth",
    # 1 Samuel
    "1 Sam.": "1 Samuel",
    "1 Sam": "1 Samuel",
    "1 Samuel": "1 Samuel",
    # 2 Samuel
    "2 Sam.": "2 Samuel",
    "2 Sam": "2 Samuel",
    "2 Samuel": "2 Samuel",
    # 1 Kings
    "1 Kings": "1 Kings",
    "1 Ki.": "1 Kings",
    "1 Ki": "1 Kings",
    "1 King": "1 Kings",
    # 2 Kings
    "2 Kings": "2 Kings",
    "2 Ki.": "2 Kings",
    "2 Ki": "2 Kings",
    "2 King": "2 Kings",
    # 1 Chronicles
    "1 Chron.": "1 Chronicles",
    "1 Chron": "1 Chronicles",
    "1 Ch.": "1 Chronicles",
    "1 Ch": "1 Chronicles",
    "1 Chronicles": "1 Chronicles",
    # 2 Chronicles
    "2 Chron.": "2 Chronicles",
    "2 Chron": "2 Chronicles",
    "2 Ch.": "2 Chronicles",
    "2 Ch": "2 Chronicles",
    "2 Chronicles": "2 Chronicles",
    # Ezra
    "Ezra": "Ezra",
    # Nehemiah
    "Neh.": "Nehemiah",
    "Neh": "Nehemiah",
    "Nehemiah": "Nehemiah",
    # Esther
    "Esth.": "Esther",
    "Esth": "Esther",
    "Esther": "Esther",
    # Job
    "Job": "Job",
    # Psalms
    "Ps.": "Psalms",
    "Ps": "Psalms",
    "Pss.": "Psalms",
    "Pss": "Psalms",
    "Psalm": "Psalms",
    "Psalms": "Psalms",
    # Proverbs
    "Prov.": "Proverbs",
    "Prov": "Proverbs",
    "Pr.": "Proverbs",
    "Pr": "Proverbs",
    "Proverbs": "Proverbs",
    # Ecclesiastes
    "Eccl.": "Ecclesiastes",
    "Eccl": "Ecclesiastes",
    "Ec.": "Ecclesiastes",
    "Ec": "Ecclesiastes",
    "Ecclesiastes": "Ecclesiastes",
    # Song of Solomon
    "Song of Sol.": "Song of Solomon",
    "Song of Sol": "Song of Solomon",
    "Song of Songs": "Song of Solomon",
    "Song": "Song of Solomon",
    "Cant.": "Song of Solomon",
    "Canticles": "Song of Solomon",
    # Isaiah
    "Isa.": "Isaiah",
    "Isa": "Isaiah",
    "Isaiah": "Isaiah",
    # Jeremiah
    "Jer.": "Jeremiah",
    "Jer": "Jeremiah",
    "Jeremiah": "Jeremiah",
    # Lamentations
    "Lam.": "Lamentations",
    "Lam": "Lamentations",
    "Lamentations": "Lamentations",
    # Ezekiel
    "Ezek.": "Ezekiel",
    "Ezek": "Ezekiel",
    "Ezekiel": "Ezekiel",
    # Daniel
    "Dan.": "Daniel",
    "Dan": "Daniel",
    "Daniel": "Daniel",
    # Hosea
    "Hos.": "Hosea",
    "Hos": "Hosea",
    "Hosea": "Hosea",
    # Joel
    "Joel": "Joel",
    # Amos
    "Amos": "Amos",
    # Obadiah
    "Obad.": "Obadiah",
    "Obad": "Obadiah",
    "Ob.": "Obadiah",
    "Ob": "Obadiah",
    "Obadiah": "Obadiah",
    # Jonah
    "Jonah": "Jonah",
    "Jon.": "Jonah",
    "Jon": "Jonah",
    # Micah
    "Mic.": "Micah",
    "Mic": "Micah",
    "Micah": "Micah",
    # Nahum
    "Nah.": "Nahum",
    "Nah": "Nahum",
    "Nahum": "Nahum",
    # Habakkuk
    "Hab.": "Habakkuk",
    "Hab": "Habakkuk",
    "Habakkuk": "Habakkuk",
    # Zephaniah
    "Zeph.": "Zephaniah",
    "Zeph": "Zephaniah",
    "Zephaniah": "Zephaniah",
    # Haggai
    "Hag.": "Haggai",
    "Hag": "Haggai",
    "Haggai": "Haggai",
    # Zechariah
    "Zech.": "Zechariah",
    "Zech": "Zechariah",
    "Zechariah": "Zechariah",
    # Malachi
    "Mal.": "Malachi",
    "Mal": "Malachi",
    "Malachi": "Malachi",
    # Matthew
    "Matt.": "Matthew",
    "Matt": "Matthew",
    "Mt.": "Matthew",
    "Mt": "Matthew",
    "Matthew": "Matthew",
    # Mark
    "Mark": "Mark",
    "Mr.": "Mark",
    "Mr": "Mark",
    # Luke
    "Luke": "Luke",
    "Lu.": "Luke",
    "Lu": "Luke",
    # John
    "John": "John",
    "Joh.": "John",
    "Joh": "John",
    # Acts
    "Acts": "Acts",
    "Ac.": "Acts",
    "Ac": "Acts",
    # Romans
    "Rom.": "Romans",
    "Rom": "Romans",
    "Ro.": "Romans",
    "Ro": "Romans",
    "Romans": "Romans",
    # 1 Corinthians
    "1 Cor.": "1 Corinthians",
    "1 Cor": "1 Corinthians",
    "1 Co.": "1 Corinthians",
    "1 Co": "1 Corinthians",
    "1 Corinthians": "1 Corinthians",
    # 2 Corinthians
    "2 Cor.": "2 Corinthians",
    "2 Cor": "2 Corinthians",
    "2 Co.": "2 Corinthians",
    "2 Co": "2 Corinthians",
    "2 Corinthians": "2 Corinthians",
    # Galatians
    "Gal.": "Galatians",
    "Gal": "Galatians",
    "Galatians": "Galatians",
    # Ephesians
    "Eph.": "Ephesians",
    "Eph": "Ephesians",
    "Ephesians": "Ephesians",
    # Philippians
    "Phil.": "Philippians",
    "Phil": "Philippians",
    "Philippians": "Philippians",
    # Colossians
    "Col.": "Colossians",
    "Col": "Colossians",
    "Colossians": "Colossians",
    # 1 Thessalonians
    "1 Thess.": "1 Thessalonians",
    "1 Thess": "1 Thessalonians",
    "1 Th.": "1 Thessalonians",
    "1 Th": "1 Thessalonians",
    "1 Thessalonians": "1 Thessalonians",
    # 2 Thessalonians
    "2 Thess.": "2 Thessalonians",
    "2 Thess": "2 Thessalonians",
    "2 Th.": "2 Thessalonians",
    "2 Th": "2 Thessalonians",
    "2 Thessalonians": "2 Thessalonians",
    # 1 Timothy
    "1 Tim.": "1 Timothy",
    "1 Tim": "1 Timothy",
    "1 Ti.": "1 Timothy",
    "1 Ti": "1 Timothy",
    "1 Timothy": "1 Timothy",
    # 2 Timothy
    "2 Tim.": "2 Timothy",
    "2 Tim": "2 Timothy",
    "2 Ti.": "2 Timothy",
    "2 Ti": "2 Timothy",
    "2 Timothy": "2 Timothy",
    # Titus
    "Titus": "Titus",
    "Tit.": "Titus",
    "Tit": "Titus",
    # Philemon
    "Philem.": "Philemon",
    "Philem": "Philemon",
    "Phm.": "Philemon",
    "Phm": "Philemon",
    "Philemon": "Philemon",
    # Hebrews
    "Heb.": "Hebrews",
    "Heb": "Hebrews",
    "Hebrews": "Hebrews",
    # James
    "Jas.": "James",
    "Jas": "James",
    "James": "James",
    # 1 Peter
    "1 Pet.": "1 Peter",
    "1 Pet": "1 Peter",
    "1 Pe.": "1 Peter",
    "1 Pe": "1 Peter",
    "1 Peter": "1 Peter",
    # 2 Peter
    "2 Pet.": "2 Peter",
    "2 Pet": "2 Peter",
    "2 Pe.": "2 Peter",
    "2 Pe": "2 Peter",
    "2 Peter": "2 Peter",
    # 1 John
    "1 John": "1 John",
    "1 Joh.": "1 John",
    "1 Joh": "1 John",
    "1 Jo.": "1 John",
    "1 Jo": "1 John",
    # 2 John
    "2 John": "2 John",
    "2 Joh.": "2 John",
    "2 Joh": "2 John",
    "2 Jo.": "2 John",
    "2 Jo": "2 John",
    # 3 John
    "3 John": "3 John",
    "3 Joh.": "3 John",
    "3 Joh": "3 John",
    "3 Jo.": "3 John",
    "3 Jo": "3 John",
    # Jude
    "Jude": "Jude",
    # Revelation
    "Rev.": "Revelation",
    "Rev": "Revelation",
    "Re.": "Revelation",
    "Re": "Revelation",
    "Revelation": "Revelation",
}


def expand_bible_citation(citation: str) -> str:
    """Expand abbreviated Bible book name to full proper name."""
    clean_citation = citation.replace("\u200b", "").strip().rstrip(".")
    for abbr, full_name in sorted(
        BIBLE_BOOKS.items(), key=lambda x: len(x[0]), reverse=True
    ):
        if clean_citation.startswith(abbr):
            remainder = clean_citation[len(abbr) :]
            if remainder and remainder[0].isalpha():
                continue
            cleaned_remainder = remainder.lstrip(". ")
            if cleaned_remainder:
                return f"{full_name} {cleaned_remainder}"
            return full_name
    return clean_citation


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
        self._language = language

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
