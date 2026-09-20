from __future__ import annotations

import unicodedata

import pytest

from numeralform import DecimalNumber, DigitSequence, render, supports

COUNT_WORDS = {
    "bg": (
        "едно",
        "две",
        "три",
        "четири",
        "пет",
        "шест",
        "седем",
        "осем",
        "девет",
        "десет",
    ),
    "el": (
        "ένα",
        "δύο",
        "τρία",
        "τέσσερα",
        "πέντε",
        "έξι",
        "επτά",
        "οκτώ",
        "εννέα",
        "δέκα",
    ),
    "et": (
        "üks",
        "kaks",
        "kolm",
        "neli",
        "viis",
        "kuus",
        "seitse",
        "kaheksa",
        "üheksa",
        "kümme",
    ),
    "eu": (
        "bat",
        "bi",
        "hiru",
        "lau",
        "bost",
        "sei",
        "zazpi",
        "zortzi",
        "bederatzi",
        "hamar",
    ),
    "ka": (
        "ერთი",
        "ორი",
        "სამი",
        "ოთხი",
        "ხუთი",
        "ექვსი",
        "შვიდი",
        "რვა",
        "ცხრა",
        "ათი",
    ),
    "ku": ("yek", "du", "sê", "çar", "pênc", "şeş", "heft", "heşt", "neh", "deh"),
    "lb": (
        "eent",
        "zwee",
        "dräi",
        "véier",
        "fënnef",
        "sechs",
        "siwen",
        "aacht",
        "néng",
        "zéng",
    ),
    "ml": ("ഒന്ന്", "രണ്ട്", "മൂന്ന്", "നാല്", "അഞ്ച്", "ആറ്", "ഏഴ്", "എട്ട്", "ഒൻപത്", "പത്ത്"),
    "mr": ("एक", "दोन", "तीन", "चार", "पाच", "सहा", "सात", "आठ", "नऊ", "दहा"),
    "ne": ("एक", "दुई", "तिन", "चार", "पाँच", "छ", "सात", "आठ", "नौ", "दस"),
    "sq": (
        "një",
        "dy",
        "tre",
        "katër",
        "pesë",
        "gjashtë",
        "shtatë",
        "tetë",
        "nëntë",
        "dhjetë",
    ),
    "sw": (
        "moja",
        "mbili",
        "tatu",
        "nne",
        "tano",
        "sita",
        "saba",
        "nane",
        "tisa",
        "kumi",
    ),
    "ur": ("ایک", "دو", "تین", "چار", "پانچ", "چھ", "سات", "آٹھ", "نو", "دس"),
}


@pytest.mark.parametrize(("locale", "expected"), COUNT_WORDS.items())
def test_reviewed_count_words(locale: str, expected: tuple[str, ...]) -> None:
    assert tuple(render(i, locale=locale) for i in range(1, 11)) == expected


@pytest.mark.parametrize("locale", COUNT_WORDS)
def test_foundation_numeric_contract(locale: str) -> None:
    for value in (0, 42, 89, 99, 100, 101, 110, 999, 1000, 1001, 2024):
        assert render(value, locale=locale)
    assert render(DigitSequence("0010"), locale=locale, form="digits")
    assert render(DecimalNumber("1", "20"), locale=locale)
    assert supports(locale, form="cardinal", value=9_999)
    assert not supports(locale, form="cardinal", value=10_000)


@pytest.mark.parametrize("locale", COUNT_WORDS)
def test_new_outputs_are_nfc(locale: str) -> None:
    assert unicodedata.normalize("NFC", render(42, locale=locale)) == render(
        42, locale=locale
    )
