"""Bible book abbreviation mapping and expansion utilities for ha_jw_daily_text."""

from __future__ import annotations

BIBLE_BOOKS: dict[str, str] = {
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
    clean_citation = citation.replace("\u200b", "").strip().rstrip(".")
    for abbr, full_name in sorted(
        BIBLE_BOOKS.items(), key=lambda x: len(x[0]), reverse=True
    ):
        if clean_citation.startswith(abbr):
            remainder = clean_citation[len(abbr) :]
            if remainder and remainder[0].isalpha():
                continue
            cleaned_remainder = remainder.lstrip(". ").rstrip(".")
            if cleaned_remainder:
                return f"{full_name} {cleaned_remainder}"
            return full_name
    return clean_citation
