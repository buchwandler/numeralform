from __future__ import annotations

from decimal import Decimal

import pytest

from numeralform import render


@pytest.mark.parametrize(
    ("locale", "expected"),
    [
        ("de", "eins Komma zwei null"),
        ("fr", "un virgule deux zéro"),
        ("it", "uno virgola due zero"),
        ("pt", "um vírgula dois zero"),
        ("sv", "ett komma två noll"),
    ],
)
def test_canonical_decimal_fallback_uses_locale_separator(
    locale: str, expected: str
) -> None:
    assert render(Decimal("1.20"), locale=locale, form="decimal") == expected


@pytest.mark.parametrize(
    ("locale", "expected"),
    [
        ("fr-BE", "un virgule deux zéro"),
        ("it-CH", "uno virgola due zero"),
        ("pt-BR", "um vírgula dois zero"),
    ],
)
def test_regional_decimal_fallback_uses_base_locale(locale: str, expected: str) -> None:
    assert render(Decimal("1.20"), locale=locale, form="decimal") == expected


def test_canonical_decimal_keeps_visible_trailing_zero() -> None:
    assert render(Decimal("12.50"), locale="it", form="decimal").endswith("cinque zero")


@pytest.mark.parametrize(
    ("value", "locale", "expected"),
    [
        (Decimal("-0.10"), "de", "minus null Komma eins null"),
        (Decimal("-0.001"), "fr", "moins zéro virgule zéro zéro un"),
        (Decimal("-1.20"), "pt", "menos um vírgula dois zero"),
        (Decimal("0.10"), "it", "zero virgola uno zero"),
    ],
)
def test_decimal_sign_is_independent_of_integer_magnitude(value, locale, expected):
    assert render(value, locale=locale, form="decimal") == expected


def test_script_decimal_policy_avoids_inserted_spaces():
    assert render(Decimal("1.20"), locale="ja", form="decimal") == "一点二零"
    assert render(Decimal("1.20"), locale="zh", form="decimal") == "一點二零"


def test_chinese_regional_policy_controls_script_and_years():
    assert render(10_005, locale="zh-CN") == "一万零五"
    assert render(10_005, locale="zh-HK") == "一萬零五"
    assert render(415, locale="zh-CN", form="year") == "四一五"
    assert render(415, locale="zh-HK", form="year") == "四一五年"
    assert render(415, locale="zh-TW", form="year") == "四一五年"
