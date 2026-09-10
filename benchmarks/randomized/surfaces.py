"""Diagnostic surface strings for semantic randomized cases."""

from __future__ import annotations

import random
from decimal import Decimal

CURRENCY_SYMBOLS = {
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "USD": "$",
}


def _decimal_text(value: Decimal, locale: str) -> str:
    text = format(value, "f")
    if locale.split("-", 1)[0] in {"de", "es", "fi", "fr", "it", "pt", "ru", "sv"}:
        return text.replace(".", ",")
    return text


def surface_for(
    locale: str,
    kind: str,
    value: int | Decimal,
    *,
    currency: str | None = None,
    rng: random.Random | None = None,
) -> tuple[str, tuple[str, ...]]:
    """Return a readable representation that is not used for execution."""
    rng = rng or random.Random(0)
    if kind in {"cardinal", "year"}:
        return str(value), ()
    if kind == "decimal":
        return _decimal_text(value, locale), ("decimal-transport=Decimal",)
    if kind == "ordinal":
        suffix = {
            "de": ".",
            "en": "th",
            "es": ".º",
            "fr": "e",
        }.get(locale.split("-", 1)[0])
        if suffix is None:
            return str(value), ("ordinal", "surface-neutral")
        return f"{value}{suffix}", ("ordinal",)
    if kind == "currency":
        if currency is None or not isinstance(value, Decimal):
            raise ValueError("currency surface requires Decimal value and currency")
        number = _decimal_text(value, locale)
        symbol = CURRENCY_SYMBOLS.get(currency, currency)
        if rng.randrange(3) == 0:
            return f"{number} {currency}", ("currency", "iso-suffix")
        if rng.randrange(2) == 0:
            return f"{symbol}{number}", ("currency", "symbol-prefix")
        return f"{number} {symbol}", ("currency", "symbol-suffix")
    raise ValueError(f"unknown case kind: {kind!r}")


__all__ = ["CURRENCY_SYMBOLS", "surface_for"]
