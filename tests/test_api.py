# ruff: noqa: S101, PLR2004
"""Tests for the JW Daily Text API client and Bible citation expansion."""

from __future__ import annotations

import asyncio
import datetime
from unittest.mock import AsyncMock

import aiohttp
import pytest

from custom_components.ha_jw_daily_text.api import (
    DailyTextEntry,
    JWDailyTextData,
    JWTextApiClient,
    JWTextApiClientCommunicationError,
    JWTextApiClientError,
    expand_bible_citation,
)


def test_expand_bible_citation() -> None:
    """Test expanding abbreviated Bible book citations."""
    assert expand_bible_citation("Prov. 3:32") == "Proverbs 3:32"
    assert expand_bible_citation("Prov 3:32") == "Proverbs 3:32"
    assert expand_bible_citation("Gen. 18:25") == "Genesis 18:25"
    assert expand_bible_citation("1 Cor. 13:4") == "1 Corinthians 13:4"
    assert expand_bible_citation("Ps. 23:1") == "Psalms 23:1"
    assert expand_bible_citation("Psalms 23:1") == "Psalms 23:1"
    assert expand_bible_citation("Proverbs 3:32") == "Proverbs 3:32"
    assert expand_bible_citation("Song of Sol. 2:1") == "Song of Solomon 2:1"
    assert expand_bible_citation("1 Chron. 29:11") == "1 Chronicles 29:11"
    assert expand_bible_citation("Rev. 21:4") == "Revelation 21:4"
    assert expand_bible_citation("Prov. 3:32.") == "Proverbs 3:32"
    assert expand_bible_citation("UnknownBook 1:1") == "UnknownBook 1:1"
    assert expand_bible_citation("\u200bProv. 3:32 ") == "Proverbs 3:32"


def test_api_client_parse() -> None:
    """Test parsing daily text HTML into DailyTextEntry."""
    sample_html = (
        "<article>\n"
        "    <h2>Friday, September 4</h2>\n"
        '    <p class="themeScrp">'
        "Jehovah detests a devious person, but His close friendship is with "
        "the upright.\u200b—Prov. 3:32."
        "</p>\n"
        '    <div class="bodyTxt"><p>'
        "We can learn about the importance of having a sincere heart from "
        "Jesus."
        "</p></div>\n"
        "</article>"
    )
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = sample_html
    mock_session.request.return_value.__aenter__.return_value = mock_response

    client = JWTextApiClient(session=mock_session, language="lp-e")
    entry = asyncio.run(client.async_get_entry_for_date(datetime.date(2026, 9, 4)))

    assert isinstance(entry, DailyTextEntry)
    assert entry.date == "2026-09-04"
    assert entry.day_and_date == "Friday, September 4"
    assert entry.scripture_text == (
        "Jehovah detests a devious person, but His close friendship is "
        "with the upright."
    )
    assert entry.scripture == "Proverbs 3:32"
    assert (
        entry.comments
        == "We can learn about the importance of having a sincere heart from Jesus."
    )


def test_api_client_parse_strips_publication_ref() -> None:
    """Test commentary parsing strips trailing publication references."""
    sample_html = (
        "<article>\n"
        "    <h2>Saturday, September 5</h2>\n"
        '    <p class="themeScrp">Love is patient and kind.\u200b—1 Cor. 13:4.</p>\n'
        '    <div class="bodyTxt">\n'
        "        <p>Cultivating patience brings joy to those around us. "
        '<a href="#">w24.06 10 ¶7, 9</a></p>\n'
        "    </div>\n"
        "</article>"
    )
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = sample_html
    mock_session.request.return_value.__aenter__.return_value = mock_response

    client = JWTextApiClient(session=mock_session, language="lp-e")
    entry = asyncio.run(client.async_get_entry_for_date(datetime.date(2026, 9, 5)))

    assert entry.comments == "Cultivating patience brings joy to those around us."


def test_api_client_parse_hyphen_in_verse() -> None:
    """Test that hyphens inside verse text do not break citation splitting."""
    sample_html = (
        "<article>\n"
        "    <h2>Sunday, September 6</h2>\n"
        '    <p class="themeScrp">Love is not quick-tempered.\u200b—1 Cor. 13:5.</p>\n'
        '    <div class="bodyTxt"><p>Commentary text here.</p></div>\n'
        "</article>"
    )
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = sample_html
    mock_session.request.return_value.__aenter__.return_value = mock_response

    client = JWTextApiClient(session=mock_session, language="lp-e")
    entry = asyncio.run(client.async_get_entry_for_date(datetime.date(2026, 9, 6)))

    assert entry.scripture_text == "Love is not quick-tempered."
    assert entry.scripture == "1 Corinthians 13:5"


def test_api_client_parse_missing_elements() -> None:
    """Test parsing gracefully handles missing HTML elements."""
    sample_html = "<article><p>Empty article</p></article>"
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = sample_html
    mock_session.request.return_value.__aenter__.return_value = mock_response

    client = JWTextApiClient(session=mock_session)
    entry = asyncio.run(client.async_get_entry_for_date(datetime.date(2026, 9, 4)))

    assert entry.date == "2026-09-04"
    assert entry.day_and_date == "Daily Text"
    assert entry.scripture_text == ""
    assert entry.scripture == ""
    assert entry.comments == ""


def test_api_client_languages() -> None:
    """Test URL prefix generation for supported languages."""
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = "<article></article>"
    mock_session.request.return_value.__aenter__.return_value = mock_response

    client_es = JWTextApiClient(session=mock_session, language="lp-s")
    asyncio.run(client_es.async_get_entry_for_date(datetime.date(2026, 9, 4)))
    call_url_es = mock_session.request.call_args[1]["url"]
    assert call_url_es == "https://wol.jw.org/es/wol/dt/r1/lp-s/2026/09/04"

    client_fr = JWTextApiClient(session=mock_session, language="lp-f")
    asyncio.run(client_fr.async_get_entry_for_date(datetime.date(2026, 9, 4)))
    call_url_fr = mock_session.request.call_args[1]["url"]
    assert call_url_fr == "https://wol.jw.org/fr/wol/dt/r1/lp-f/2026/09/04"

    client_de = JWTextApiClient(session=mock_session, language="lp-x")
    asyncio.run(client_de.async_get_entry_for_date(datetime.date(2026, 9, 4)))
    call_url_de = mock_session.request.call_args[1]["url"]
    assert call_url_de == "https://wol.jw.org/de/wol/dt/r1/lp-x/2026/09/04"

    client_pt = JWTextApiClient(session=mock_session, language="lp-po")
    asyncio.run(client_pt.async_get_entry_for_date(datetime.date(2026, 9, 4)))
    call_url_pt = mock_session.request.call_args[1]["url"]
    assert call_url_pt == "https://wol.jw.org/pt/wol/dt/r1/lp-po/2026/09/04"


def test_async_get_daily_text_data() -> None:
    """Test fetching yesterday, today, and tomorrow in parallel."""
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = (
        "<article>\n"
        "    <h2>Friday, September 4</h2>\n"
        '    <p class="themeScrp">Theme.\u200b—Prov. 3:32.</p>\n'
        '    <div class="bodyTxt"><p>Comment.</p></div>\n'
        "</article>"
    )
    mock_session.request.return_value.__aenter__.return_value = mock_response

    client = JWTextApiClient(session=mock_session, language="lp-e")
    data = asyncio.run(client.async_get_daily_text_data(datetime.date(2026, 9, 4)))

    assert isinstance(data, JWDailyTextData)
    assert data.yesterday.date == "2026-09-03"
    assert data.today.date == "2026-09-04"
    assert data.tomorrow.date == "2026-09-05"
    assert mock_session.request.call_count == 3


def test_api_client_http_error() -> None:
    """Test that HTTP status errors raise JWTextApiClientCommunicationError."""
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_response = AsyncMock()
    mock_response.status = 404
    mock_session.request.return_value.__aenter__.return_value = mock_response

    client = JWTextApiClient(session=mock_session)
    with pytest.raises(JWTextApiClientCommunicationError):
        asyncio.run(client.async_get_entry_for_date(datetime.date(2026, 9, 4)))


def test_api_client_timeout() -> None:
    """Test that client errors or timeouts raise JWTextApiClientCommunicationError."""
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_session.request.side_effect = TimeoutError("Connection timed out")

    client = JWTextApiClient(session=mock_session)
    with pytest.raises(JWTextApiClientCommunicationError):
        asyncio.run(client.async_get_entry_for_date(datetime.date(2026, 9, 4)))


def test_exception_hierarchy() -> None:
    """Test exception inheritance."""
    assert issubclass(JWTextApiClientCommunicationError, JWTextApiClientError)
    assert issubclass(JWTextApiClientError, Exception)
