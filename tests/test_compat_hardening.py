from __future__ import annotations

from decimal import Decimal

import pytest

from numeralform.compat import num2words
from numeralform.compat.num2words import (
    _apply_precision,
    _coerce_legacy_number,
    _compat_decimal,
    _decimal_number,
    _legacy_cardinal,
    _legacy_currency,
    _legacy_decimal,
    _legacy_english_cardinal,
    _legacy_english_ordinal,
    _legacy_has_explicit_fraction,
    _legacy_japanese_year,
    _legacy_russian_decimal,
    _legacy_spanish_ordinal,
    _ordinal_numeric,
    _render_decimal,
    _resolve_legacy_lang,
    _translate_kwargs,
)
from numeralform.errors import InvalidRequestError
from numeralform.model import DecimalNumber, FractionNumber


def test_legacy_number_coercion_and_precision_contract():
    assert _coerce_legacy_number(True) == 1
    assert _coerce_legacy_number(3) == 3
    assert isinstance(_coerce_legacy_number(Decimal("1.20")), DecimalNumber)
    assert isinstance(_coerce_legacy_number(1.2), DecimalNumber)
    assert isinstance(_coerce_legacy_number("2/3"), FractionNumber)
    assert _coerce_legacy_number(" 42 ") == 42
    assert isinstance(_coerce_legacy_number("1.20"), DecimalNumber)
    assert _coerce_legacy_number(object()) is not None
    with pytest.raises(TypeError):
        _coerce_legacy_number("not numeric")
    with pytest.raises(TypeError):
        _coerce_legacy_number(float("inf"))
    with pytest.raises(TypeError):
        _decimal_number(Decimal("NaN"))

    assert _apply_precision(DecimalNumber("1", "25"), 1).fraction == "3"
    assert _apply_precision(1, 2).fraction == "00"
    assert _apply_precision(FractionNumber(1, 2), 2) == FractionNumber(1, 2)
    with pytest.raises(TypeError):
        _apply_precision(1, True)


def test_legacy_locale_resolution_and_cardinal_variants():
    assert _resolve_legacy_lang("en_US").numeralform_locale == "en"
    assert _legacy_english_cardinal(1001, "en") == "one thousand and one"
    assert _legacy_english_cardinal(100, "en") == "one hundred"
    assert _legacy_english_cardinal(100_001, "en-IN")
    assert _legacy_english_cardinal(10_000_000, "en-IN")
    assert _legacy_cardinal(100, "pt-BR")
    assert _legacy_cardinal(200_100, "pt")
    assert _legacy_cardinal(10_000, "ko")
    assert _legacy_cardinal(1000, "sv")
    assert _legacy_cardinal(3, "it")
    assert _legacy_cardinal(1_000_003, "it")
    assert _legacy_cardinal(80000, "fr-BE")
    assert _legacy_cardinal(80000, "fr")
    assert _legacy_cardinal(1001, "vi")
    assert _legacy_cardinal(2_000_000, "cs")


def test_legacy_decimal_and_fraction_paths():
    assert _legacy_decimal(DecimalNumber("12", "500"), "en")
    assert _legacy_decimal(DecimalNumber("12", "50", True), "en")
    assert _compat_decimal(DecimalNumber("12", "50"), "en", {})
    assert _compat_decimal(DecimalNumber("12", "50"), "ru", {})
    assert _compat_decimal(DecimalNumber("12", "50"), "es", {})
    assert _compat_decimal(DecimalNumber("12", "50"), "en", {"style": "british-and"})
    assert _render_decimal(DecimalNumber("12", "50"), "en", {})
    assert _legacy_has_explicit_fraction(1.5)
    assert _legacy_has_explicit_fraction(DecimalNumber("1", "0"))
    assert not _legacy_has_explicit_fraction(1)
    assert _legacy_russian_decimal(DecimalNumber("1", "1"))
    assert _legacy_russian_decimal(DecimalNumber("2", "22", True))


def test_legacy_year_ordinal_and_numeric_ordinal_variants():
    assert _legacy_japanese_year(2019)
    assert _legacy_japanese_year(1900)
    assert _legacy_english_ordinal(100)
    assert _legacy_english_ordinal(101)
    assert _legacy_spanish_ordinal(0) == ""
    assert _legacy_spanish_ordinal(20)
    assert _legacy_spanish_ordinal(1001)
    for locale in ("en", "es", "fr", "eo", "fa", "ja", "zh", "pt", "de", "fi"):
        assert _ordinal_numeric(1, locale, {})
    assert _ordinal_numeric(1, "es", {"gender": "feminine"}) == "1ª"


def test_legacy_currency_language_and_scale_variants():
    cases = (
        ("en", "EUR", Decimal("1.01")),
        ("en", "GBP", Decimal("2.02")),
        ("cs", "EUR", Decimal("2.02")),
        ("de", "EUR", Decimal("1.01")),
        ("es", "EUR", Decimal("1.01")),
        ("fi", "GBP", Decimal("1.01")),
        ("fr", "EUR", Decimal("2.02")),
        ("it", "EUR", Decimal("1.01")),
        ("pt", "EUR", Decimal("2.02")),
        ("ru", "RUB", Decimal("22.02")),
        ("th", "EUR", Decimal("1.01")),
        ("ko", "EUR", Decimal("1.01")),
    )
    for locale, currency, value in cases:
        assert _legacy_currency(value, locale, currency, True, None, value)
        assert _legacy_currency(value, locale, currency, False, ",", value)
    assert _legacy_currency(Decimal("61.0"), "en", "JPY", True, None, Decimal("61.0"))
    assert _legacy_currency(Decimal("1.001"), "en", "KWD", True, None, Decimal("1.001"))
    assert _legacy_currency(Decimal("-2.01"), "ru", "RUB", True, None, Decimal("-2.01"))
    assert _legacy_currency(Decimal("1.01"), "en", "CAD", True, None, Decimal("1.01"))


def test_legacy_option_translation_and_public_entry_paths():
    assert _translate_kwargs({"gender": "m", "plural": True, "animate": False})
    with pytest.raises(InvalidRequestError):
        _translate_kwargs({"unexpected": True})

    assert num2words("0042", lang="en")
    assert num2words("2/3", lang="en", to="fraction")
    assert num2words(Decimal("1.25"), lang="en", precision=1)
    assert num2words(2024, lang="ja", to="year")
    assert num2words(21, lang="sv", to="ordinal")
    assert num2words(21, lang="it", to="ordinal")
    assert num2words(21, lang="fr", to="ordinal")
    assert num2words(21, lang="ru", to="ordinal")
    assert num2words(2, lang="es", to="ordinal_num", gender="feminine") == "2ª"
    assert num2words(1, lang="en", style="num2words")
    with pytest.raises(TypeError):
        num2words(1, lang="")
    with pytest.raises(NotImplementedError):
        num2words(1, to="missing")
    with pytest.raises(InvalidRequestError):
        num2words(1, currency="EUR")
