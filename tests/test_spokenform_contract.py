from __future__ import annotations

import unicodedata

import pytest

from numeralform import (
    DecimalNumber,
    DigitSequence,
    locales,
    render,
    resolve_locale,
    supports,
)

SPOKENFORM_BASES = frozenset(
    [
        "am",
        "ar",
        "az",
        "be",
        "bn",
        "ca",
        "ce",
        "cs",
        "cy",
        "da",
        "de",
        "en",
        "eo",
        "es",
        "fa",
        "fi",
        "fr",
        "he",
        "hi",
        "hu",
        "hy",
        "id",
        "is",
        "it",
        "ja",
        "kk",
        "kn",
        "ko",
        "lt",
        "lv",
        "mn",
        "nl",
        "no",
        "pl",
        "pt",
        "ro",
        "ru",
        "sk",
        "sl",
        "sr",
        "sv",
        "te",
        "tet",
        "tg",
        "th",
        "tr",
        "uk",
        "vi",
        "zh",
    ]
)
SPOKENFORM_REGIONAL = frozenset(
    [
        "en-GB",
        "en-IN",
        "en-NG",
        "en-US",
        "es-CO",
        "es-CR",
        "es-GT",
        "es-MX",
        "es-NI",
        "es-VE",
        "fr-BE",
        "fr-CH",
        "fr-DZ",
        "pt-BR",
        "zh-CN",
        "zh-HK",
        "zh-TW",
    ]
)


def test_spokenform_base_contract_is_executable() -> None:
    assert SPOKENFORM_BASES <= set(locales())
    for locale in sorted(SPOKENFORM_BASES):
        assert supports(locale, form="cardinal", value=42)
        assert render(42, locale=locale)
        assert render(DigitSequence("0042"), locale=locale)
        assert supports(locale, form="decimal", value=DecimalNumber("1", "20"))
        assert render(DecimalNumber("1", "20"), locale=locale)
        assert render(2024, locale=locale, form="year")


@pytest.mark.parametrize("locale", sorted(SPOKENFORM_REGIONAL))
def test_spokenform_regional_contract_is_exact(locale: str) -> None:
    assert locale in locales()
    assert resolve_locale(locale) == locale
    assert render(42, locale=locale)


def test_canonical_outputs_are_nfc() -> None:
    for locale in sorted(SPOKENFORM_BASES | SPOKENFORM_REGIONAL):
        for value in (0, 42, 2024):
            text = render(value, locale=locale)
            assert unicodedata.normalize("NFC", text) == text


def test_kazakh_uses_canonical_bcp47_identity() -> None:
    from numeralform.compat import num2words
    from numeralform.compat._num2words.registry import resolve_compat_locale

    assert "kk" in locales()
    assert "kz" not in locales()
    assert resolve_compat_locale("kz").resolution.numeralform_locale == "kk"
    assert num2words(42, lang="kz")


def test_korean_word_and_numeric_ordinals_are_distinct() -> None:
    assert render(3, locale="ko", form="ordinal") == "세 번째"
    assert render(3, locale="ko", form="ordinal_num") == "3번째"
