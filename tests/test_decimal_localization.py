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
