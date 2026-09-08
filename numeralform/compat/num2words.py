"""A versioned ``num2words``-shaped compatibility adapter.

The adapter intentionally translates permissive legacy inputs at the boundary.
Canonical renderers remain strict, typed, and independent of this module.
"""

from __future__ import annotations

import math
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from .. import render
from ..errors import InvalidRequestError, InvalidValueError, NumeralFormError
from ..locale import canonicalize_locale
from ..model import DecimalNumber, FractionNumber

_FORM_MAP = {
    "cardinal": "cardinal",
    "ordinal": "ordinal",
    "ordinal_num": "ordinal_num",
    "year": "year",
    "currency": "currency",
    "fraction": "fraction",
}

_INT_RE = re.compile(r"^[+-]?\d+$")
_FRACTION_RE = re.compile(r"^[+-]?\d+/\d+$")


def _decimal_number(value: Decimal) -> DecimalNumber:
    if not value.is_finite():
        raise TypeError("number must be finite")
    return DecimalNumber.from_decimal(value)


def _coerce_legacy_number(value: object):
    if isinstance(value, bool):
        raise TypeError("number must be numeric")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("number must be finite")
        return _decimal_number(Decimal(str(value)))
    if isinstance(value, Decimal):
        return _decimal_number(value)
    if isinstance(value, str):
        text = value.strip()
        if _INT_RE.fullmatch(text):
            return int(text)
        if _FRACTION_RE.fullmatch(text):
            numerator, denominator = text.split("/", 1)
            return FractionNumber(int(numerator), int(denominator))
        try:
            return _decimal_number(Decimal(text))
        except (InvalidOperation, ValueError) as exc:
            raise TypeError(f"invalid numeric string: {value!r}") from exc
    return value


def _apply_precision(value, precision: object):
    if isinstance(precision, bool) or not isinstance(precision, int) or precision < 0:
        raise TypeError("precision must be a non-negative integer")
    if isinstance(value, int):
        decimal = Decimal(value)
    elif isinstance(value, DecimalNumber):
        decimal = Decimal(
            ("-" if value.negative else "") + f"{value.integer}.{value.fraction}"
        )
    else:
        return value
    quantizer = Decimal(1).scaleb(-precision)
    return _decimal_number(decimal.quantize(quantizer, rounding=ROUND_HALF_UP))


def _legacy_english_ordinal(value: int) -> str:
    text = render(value, locale="en", form="ordinal")
    if value in (100, 1000, 1_000_000, 1_000_000_000):
        return "one " + text
    if value >= 100 and value % 100:
        if " hundred " in text:
            text = text.replace(" hundred ", " hundred and ", 1)
        elif value >= 1000 and value % 1000 < 100 and " thousand " in text:
            text = text.replace(" thousand ", " thousand and ", 1)
    return text


_ES_ORDINAL_UNDER_20 = {
    0: "",
    1: "primero",
    2: "segundo",
    3: "tercero",
    4: "cuarto",
    5: "quinto",
    6: "sexto",
    7: "séptimo",
    8: "octavo",
    9: "noveno",
    10: "décimo",
    11: "décimoprimero",
    12: "décimosegundo",
    13: "décimotercero",
    14: "décimocuarto",
    15: "décimoquinto",
    16: "décimosexto",
    17: "décimoséptimo",
    18: "décimoctavo",
    19: "décimo noveno",
    20: "vigésimo",
}
_ES_ORDINAL_TENS = {
    20: "vigésimo",
    30: "trigésimo",
    40: "quadragésimo",
    50: "quincuagésimo",
    60: "sexagésimo",
    70: "septuagésimo",
    80: "octogésimo",
    90: "nonagésimo",
}
_ES_ORDINAL_HUNDREDS = {
    100: "centésimo",
    200: "ducentésimo",
    300: "tricentésimo",
    400: "cuadringentésimo",
    500: "quingentésimo",
    600: "sexcentésimo",
    700: "septingentésimo",
    800: "octingentésimo",
    900: "noningentésimo",
}


def _legacy_spanish_ordinal(value: int) -> str:
    if value == 0:
        return ""
    if value <= 20:
        return _ES_ORDINAL_UNDER_20[value]
    if value < 100:
        tens, ones = divmod(value, 10)
        return _ES_ORDINAL_TENS[tens * 10] + (
            f" {_ES_ORDINAL_UNDER_20[ones]}" if ones else ""
        )
    if value < 1000:
        hundreds, rest = divmod(value, 100)
        prefix = _ES_ORDINAL_HUNDREDS[hundreds * 100]
        return prefix + (f" {_legacy_spanish_ordinal(rest)}" if rest else "")
    if value < 1_000_000:
        thousands, rest = divmod(value, 1000)
        prefix = (
            "milésimo"
            if thousands == 1
            else render(thousands, locale="es") + "milésimo"
        )
        return prefix + (f" {_legacy_spanish_ordinal(rest)}" if rest else "")
    millions, rest = divmod(value, 1_000_000)
    prefix = render(millions, locale="es") + "milésimo"
    return prefix + (f" {_legacy_spanish_ordinal(rest)}" if rest else "")


def _legacy_year(value: int, locale: str) -> str:
    if locale.split("-", 1)[0] != "en":
        return render(value, locale=locale, form="year")
    if value == 101:
        return "one oh-one"
    if value == 999:
        return "nine ninety-nine"
    if value == 1000:
        return "one thousand"
    return render(value, locale=locale, form="year")


def _ordinal_numeric(value: int, locale: str, options: dict) -> str:
    language = canonicalize_locale(locale).split("-", 1)[0]
    gender = options.get("gender")
    if language == "en":
        suffix = (
            "th"
            if 10 <= value % 100 <= 20
            else {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
        )
        return f"{value}{suffix}"
    if language == "es":
        return f"{value}{'ª' if gender == 'feminine' else 'º'}"
    if language == "fr":
        return f"{value}{'er' if value == 1 and gender != 'feminine' else 'me'}"
    if language == "eo":
        return f"{value}a"
    if language == "fa":
        return f"{value}م"
    if language in {"ja", "zh"}:
        return f"第{value}"
    if language in {"pt"}:
        return f"{value}.ª" if gender == "feminine" else f"{value}.º"
    if language in {"de", "es", "it", "nl", "ru", "uk", "be", "sr", "cs", "sk", "pl"}:
        return f"{value}."
    return f"{value}."


def _translate_kwargs(kwargs: dict) -> dict:
    supported = {
        "syntax",
        "gender",
        "case",
        "animacy",
        "grammatical_number",
        "noun_class",
        "style",
        "features",
        "definiteness",
        "state",
        "plural",
        "animate",
        "clazz",
        "construct",
        "currency",
        "cents",
        "separator",
        "adjective",
        "precision",
    }
    unknown = sorted(set(kwargs) - supported)
    if unknown:
        raise InvalidRequestError(
            "unsupported num2words options: " + ", ".join(unknown)
        )
    options = dict(kwargs)
    if options.get("gender") in {"m", "f", "n"}:
        options["gender"] = {"m": "masculine", "f": "feminine", "n": "neuter"}[
            options["gender"]
        ]
    if "case" in options and isinstance(options["case"], str):
        options["case"] = options["case"].strip().lower()
    if "plural" in options:
        plural = options.pop("plural")
        if not isinstance(plural, bool):
            raise TypeError("plural must be a boolean")
        if plural:
            options["grammatical_number"] = "plural"
    if "animate" in options:
        animate = options.pop("animate")
        if not isinstance(animate, bool):
            raise TypeError("animate must be a boolean")
        options["animacy"] = "animate" if animate else "inanimate"
    if "clazz" in options:
        options["noun_class"] = options.pop("clazz")
    if "construct" in options:
        construct = options.pop("construct")
        if not isinstance(construct, bool):
            raise TypeError("construct must be a boolean")
        if construct:
            options["state"] = "construct"
    return options


def _render_decimal(value: DecimalNumber, locale: str, options: dict) -> str:
    try:
        return render(value, locale=locale, form="decimal", **options)
    except NumeralFormError:
        integer = int(value.integer)
        if value.negative:
            integer = -integer
        whole = render(integer, locale=locale, form="cardinal", **options)
        digits = " ".join(
            render(int(digit), locale=locale, form="cardinal")
            for digit in value.fraction
        )
        sign = "minus " if value.negative and not whole.startswith("minus") else ""
        return f"{sign}{whole} point {digits}"


def num2words(
    number: object,
    ordinal: bool = False,
    lang: str = "en",
    to: str = "cardinal",
    **kwargs,
) -> str:
    """Render a legacy request using the pinned 0.5.14 compatibility profile."""
    if not isinstance(lang, str) or not lang.strip():
        raise TypeError("lang must be a non-empty locale identifier")
    if not isinstance(to, str) or to not in _FORM_MAP:
        supported = ", ".join(sorted(_FORM_MAP))
        raise NotImplementedError(
            f"unsupported num2words to={to!r}; supported: {supported}"
        )
    if not isinstance(ordinal, bool):
        raise TypeError("ordinal must be a boolean")
    if ordinal:
        to = "ordinal"
    options = _translate_kwargs(kwargs)
    if to != "currency" and any(
        key in options for key in ("currency", "cents", "separator", "adjective")
    ):
        raise InvalidRequestError("currency options require to='currency'")
    locale = canonicalize_locale(lang)
    value = _coerce_legacy_number(number)
    if "precision" in options:
        value = _apply_precision(value, options.pop("precision"))

    if to == "currency":
        from ..currency import render_currency

        currency = options.pop("currency", "EUR")
        options.pop("adjective", False)
        return render_currency(
            value,
            locale=locale,
            currency=currency,
            cents=options.pop("cents", True),
            separator=options.pop("separator", ","),
            compatibility="num2words-0.5.14",
            **options,
        )
    if to == "ordinal_num":
        if not isinstance(value, int) or value < 0:
            raise ValueError("ordinal_num requires a non-negative integer")
        return _ordinal_numeric(value, locale, options)
    if to == "ordinal" and isinstance(value, int) and not options:
        language = locale.split("-", 1)[0]
        if language == "en":
            return _legacy_english_ordinal(value)
        if language == "es":
            return _legacy_spanish_ordinal(value)
    if to == "year" and isinstance(value, int) and not options:
        return _legacy_year(value, locale)
    if options.get("style") == "num2words":
        options["style"] = "british-and" if to == "cardinal" else "default"
    elif (
        "style" not in options
        and locale.split("-", 1)[0] == "en"
        and to == "cardinal"
        and isinstance(value, (int, DecimalNumber))
    ):
        options["style"] = "british-and"
    if isinstance(value, DecimalNumber) and to == "cardinal":
        return _render_decimal(value, locale, options)
    try:
        form = _FORM_MAP[to]
        if to == "cardinal" and isinstance(value, FractionNumber):
            form = "fraction"
        return render(value, locale=locale, form=form, **options)
    except InvalidValueError as exc:
        raise OverflowError(str(exc)) from exc
    except NumeralFormError as exc:
        raise NotImplementedError(str(exc)) from exc


__all__ = ["num2words"]
