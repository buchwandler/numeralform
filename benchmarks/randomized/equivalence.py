"""Narrow, auditable equivalence rules for randomized differential output."""

from __future__ import annotations

import re
import unicodedata

from .model import RandomCase

_PUNCTUATION_RE = re.compile(r"[^\w\s]", re.UNICODE)
_SPACE_RE = re.compile(r"\s+")
_SAFE_SURFACE_SHAPES = frozenset(
    {
        "hyphenation only",
        "whitespace only",
        "case only",
        "punctuation difference",
        "Unicode normalization difference",
    }
)
_EN_SMALL = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
)

# These are benchmark policy aliases, not runtime lexicon data.
_CURRENCY_RULES = {
    ("en", "EUR"): (("euro", "euros"), ("cent", "cents"), ("and",)),
    ("en", "USD"): (("dollar", "dollars"), ("cent", "cents"), ("and",)),
    ("en", "GBP"): (
        ("pound", "pounds", "pound sterling", "pounds sterling"),
        ("penny", "pence"),
        ("and",),
    ),
    ("en", "JPY"): (("yen",), ("sen",), ("and",)),
    ("cs", "EUR"): (("euro", "eura", "eur"), ("cent", "centy", "centů"), ("a",)),
    ("cs", "USD"): (("dolar", "dolary", "dolarů"), ("cent", "centy", "centů"), ("a",)),
    ("cs", "GBP"): (("libra", "libry", "liber"), ("pence", "pencí"), ("a",)),
    ("cs", "JPY"): (("jen", "yeny", "jenů"), ("sen", "sény", "senů"), ("a",)),
}


def _surface_key(text: str) -> str:
    text = unicodedata.normalize("NFC", text).casefold().replace("-", " ")
    text = _PUNCTUATION_RE.sub(" ", text)
    return _SPACE_RE.sub(" ", text).strip()


def _replace_phrase(text: str, phrase: str, marker: str) -> str:
    pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
    return re.sub(pattern, marker, text)


def _currency_key(case: RandomCase, text: str) -> str | None:
    language = case.locale.split("-", 1)[0]
    rule = _CURRENCY_RULES.get((language, case.currency or ""))
    if rule is None:
        return None
    major_aliases, minor_aliases, connector_aliases = rule
    normalized = _surface_key(text)
    for alias in sorted(major_aliases, key=len, reverse=True):
        normalized = _replace_phrase(normalized, _surface_key(alias), "<major>")
    for alias in sorted(minor_aliases, key=len, reverse=True):
        normalized = _replace_phrase(normalized, _surface_key(alias), "<minor>")
    connectors = {connector.casefold() for connector in connector_aliases}
    tokens = [token for token in normalized.split() if token not in connectors]
    return " ".join(tokens)


def _english_year_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "en" or case.kind != "year":
        return False
    value = case.python_value()
    if not isinstance(value, int):
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    if 1001 <= value <= 1009:
        unit = _EN_SMALL[value - 1000]
        allowed = {
            f"one thousand {unit}",
            f"one thousand and {unit}",
            f"ten oh {unit}",
        }
        return expected_key in allowed and actual_key in allowed
    if 2001 <= value <= 2009:
        unit = _EN_SMALL[value - 2000]
        allowed = {f"two thousand {unit}", f"two thousand and {unit}"}
        return expected_key in allowed and actual_key in allowed
    return False


def _english_decimal_precision_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.kind != "decimal" or case.locale.split("-", 1)[0] != "en":
        return False
    _, fraction = (
        case.value.value.split(".", 1) if "." in case.value.value else ("", "")
    )
    trimmed = fraction.rstrip("0")
    trailing = len(fraction) - len(trimmed)
    if not trailing:
        return False
    candidate = actual
    for _ in range(trailing):
        if not candidate.endswith(" zero"):
            return False
        candidate = candidate.removesuffix(" zero")
    if not trimmed:
        if not candidate.endswith(" point"):
            return False
        candidate = candidate.removesuffix(" point")
    return _surface_key(candidate) == _surface_key(expected)


def accepted_variant(
    case: RandomCase,
    expected: str,
    actual: str,
    *,
    difference_shape: str,
) -> str | None:
    """Return the named equivalence rule when a textual difference is acceptable."""
    if difference_shape in _SAFE_SURFACE_SHAPES:
        return f"surface:{difference_shape}"
    if _english_year_variant(case, expected, actual):
        return "en-year-reading"
    if _english_decimal_precision_variant(case, expected, actual):
        return "en-decimal-trailing-zero-precision"
    if case.kind == "currency":
        expected_key = _currency_key(case, expected)
        actual_key = _currency_key(case, actual)
        if expected_key is not None and expected_key == actual_key:
            language = case.locale.split("-", 1)[0]
            return f"{language}-{case.currency.lower()}-currency"
    return None


__all__ = ["accepted_variant"]
