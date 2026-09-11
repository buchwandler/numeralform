"""Narrow, auditable equivalence rules for randomized differential output."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable

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
    ("en", "CAD"): (("dollar", "dollars", "Canadian dollar", "Canadian dollars"), ("cent", "cents"), ("and",)),
    ("en", "AUD"): (("dollar", "dollars", "Australian dollar", "Australian dollars"), ("cent", "cents"), ("and",)),
    ("en", "INR"): (("rupee", "rupees", "Indian rupee", "Indian rupees"), ("paisa", "paise"), ("and",)),
    ("en", "RUB"): (("ruble", "rubles", "rouble", "roubles"), ("kopeck", "kopecks", "kopek", "kopeks"), ("and",)),
    ("en", "SAR"): (("Saudi riyal", "Saudi riyals", "riyal", "riyals"), ("halala", "halalas"), ("and",)),
    ("en", "PLN"): (("zloty", "zlotys", "złoty", "złotys"), ("grosz", "groszy"), ("and",)),
    ("en", "JPY"): (("yen",), ("sen",), ("and",)),
    ("ru", "EUR"): (("евро",), ("цент", "цента", "центов"), ("и",)),
    ("ru", "USD"): (("доллар", "доллара", "долларов"), ("цент", "цента", "центов"), ("и",)),
    ("cs", "EUR"): (("euro", "eura", "eur"), ("cent", "centy", "centů"), ("a",)),
    ("cs", "USD"): (("dolar", "dolary", "dolarů"), ("cent", "centy", "centů"), ("a",)),
    ("cs", "GBP"): (("libra", "libry", "liber"), ("pence", "pencí"), ("a",)),
    ("cs", "JPY"): (("jen", "yeny", "jenů"), ("sen", "sény", "senů"), ("a",)),
}

_ES_ORDINAL_VARIANTS = {
    11: {"undécimo", "decimoprimero", "décimo primero"},
    12: {"duodécimo", "decimosegundo", "décimo segundo"},
}
_ES_ORDINAL_ACCENT_VARIANTS = {20: ("vigesimo", "vigésimo")}
_FR_CONTINUATION_WORDS = frozenset(
    {
        "un", "une", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
        "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "vingt",
        "trente", "quarante", "cinquante", "soixante", "septante", "huitante", "nonante",
        "et", "premier", "première", "deuxième", "troisième", "quatrième",
    }
)


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


def _english_under_100(value: int) -> str:
    if value < 20:
        return ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen")[value]
    tens = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")[value // 10]
    return tens if value % 10 == 0 else f"{tens}-{_EN_SMALL[value % 10]}"


def _english_year_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "en" or case.kind != "year":
        return False
    value = case.python_value()
    if not isinstance(value, int):
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    if 100 <= value <= 999:
        hundreds, remainder = divmod(value, 100)
        if remainder == 0:
            return False
        prefix = _EN_SMALL[hundreds]
        remainder_words = _english_under_100(remainder)
        allowed = {_surface_key(value) for value in (
            f"{prefix} {remainder_words}",
            f"{prefix} hundred {remainder_words}",
            f"{prefix} hundred and {remainder_words}",
        )}
        return expected_key in allowed and actual_key in allowed
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


def _decimal_trailing_zero_precision_variant(case: RandomCase, expected: str, actual: str) -> bool:
    language = case.locale.split("-", 1)[0]
    decimal_words = {
        "en": ("point", "zero"),
        "es": ("punto", "cero"),
    }
    if case.kind != "decimal" or language not in decimal_words:
        return False
    marker, zero = decimal_words[language]
    _, fraction = case.value.value.split(".", 1) if "." in case.value.value else ("", "")
    trimmed = fraction.rstrip("0")
    trailing = len(fraction) - len(trimmed)
    if not trailing:
        return False
    candidate = _surface_key(actual).split()
    for _ in range(trailing):
        if not candidate or candidate[-1] != zero:
            return False
        candidate.pop()
    if not trimmed:
        if not candidate or candidate[-1] != marker:
            return False
        candidate.pop()
    return " ".join(candidate) == _surface_key(expected)


def _spanish_ordinal_accent_oracle_quirk(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "es" or case.kind != "ordinal":
        return False
    pair = _ES_ORDINAL_ACCENT_VARIANTS.get(case.python_value())
    return pair is not None and _surface_key(expected) == pair[0] and _surface_key(actual) == pair[1]


def _spanish_ordinal_synonym_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "es" or case.kind != "ordinal":
        return False
    allowed = _ES_ORDINAL_VARIANTS.get(case.python_value())
    return allowed is not None and _surface_key(expected) in {_surface_key(value) for value in allowed} and _surface_key(actual) in {_surface_key(value) for value in allowed}


def _finnish_compound_spacing_variant(case: RandomCase, expected: str, actual: str) -> bool:
    return case.locale.split("-", 1)[0] == "fi" and case.kind == "year" and "".join(expected.split()) == "".join(actual.split())


def _french_cent_oracle_quirk(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "fr" or case.kind not in {"cardinal", "ordinal", "year"}:
        return False
    tokens = _surface_key(expected).split()
    repaired = ["cent" if token == "cents" and index + 1 < len(tokens) and tokens[index + 1] in _FR_CONTINUATION_WORDS else token for index, token in enumerate(tokens)]
    return " ".join(repaired) == _surface_key(actual) and repaired != tokens


def _italian_cento_elision_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "it":
        return False
    def canonical(text: str) -> str:
        return re.sub(r"cento(?=(?:ottanta|otto|uno|undici))", "cent", _surface_key(text))
    return canonical(expected) == canonical(actual) and (canonical(expected) != _surface_key(expected) or canonical(actual) != _surface_key(actual))


def _japanese_ordinal_numeric_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "ja" or case.kind != "ordinal_num":
        return False
    value = case.python_value()
    allowed = {f"第{value}", f"{value}番目"}
    return expected in allowed and actual in allowed


def _swedish_oracle_orthography_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "sv":
        return False
    repaired = _surface_key(expected).replace("förtio", "fyrtio")
    return "".join(repaired.split()) == "".join(_surface_key(actual).split())


def _rule_registry() -> tuple[tuple[str, Callable[[RandomCase, str, str], bool]], ...]:
    return (
        ("en-year-reading", _english_year_variant),
        ("decimal-trailing-zero-precision", _decimal_trailing_zero_precision_variant),
        ("oracle:es-ordinal-accent", _spanish_ordinal_accent_oracle_quirk),
        ("variant:es-ordinal-synonym", _spanish_ordinal_synonym_variant),
        ("variant:fi-compound-spacing", _finnish_compound_spacing_variant),
        ("oracle:fr-cent-overpluralization", _french_cent_oracle_quirk),
        ("variant:it-cento-elision", _italian_cento_elision_variant),
        ("variant:ja-ordinal-notation", _japanese_ordinal_numeric_variant),
        ("oracle:sv-number-orthography", _swedish_oracle_orthography_variant),
    )


_VARIANT_RULES = _rule_registry()


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
    for name, predicate in _VARIANT_RULES:
        if predicate(case, expected, actual):
            if name == "decimal-trailing-zero-precision" and case.locale.split("-", 1)[0] == "en":
                return "en-decimal-trailing-zero-precision"
            return name
    if case.kind == "currency":
        expected_key = _currency_key(case, expected)
        actual_key = _currency_key(case, actual)
        if expected_key is not None and expected_key == actual_key:
            language = case.locale.split("-", 1)[0]
            return f"{language}-{case.currency.lower()}-currency"
    return None


__all__ = ["accepted_variant"]
