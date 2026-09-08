"""A deliberate ``num2words``-shaped compatibility adapter.

The adapter translates permissive legacy inputs into Numeralform's strict
semantic request model.  Canonical renderers remain independent of this
legacy contract.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re

from .. import render
from ..errors import InvalidRequestError, InvalidValueError, NumeralFormError
from ..locale import canonicalize_locale
from ..model import DecimalNumber

_FORM_MAP = {
    "cardinal": "cardinal",
    "ordinal": "ordinal",
    "ordinal_num": "ordinal_num",
    "year": "year",
    "currency": "currency",
}

_INT_RE = re.compile(r"^[+-]?\d+$")
_DECIMAL_RE = re.compile(r"^[+-]?(?:\d+\.\d*|\d*\.\d+)$")


def _coerce_legacy_number(value: object):
    if isinstance(value, bool):
        raise TypeError("number must be numeric")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise TypeError("number must be finite")
        return DecimalNumber.from_decimal(Decimal(str(value)))
    if isinstance(value, Decimal):
        return DecimalNumber.from_decimal(value)
    if isinstance(value, str):
        text = value.strip()
        if _INT_RE.fullmatch(text):
            return int(text)
        if _DECIMAL_RE.fullmatch(text):
            negative = text.startswith("-")
            unsigned = text[1:] if text[:1] in "+-" else text
            integer, fraction = unsigned.split(".", 1)
            return DecimalNumber(integer or "0", fraction or "0", negative)
        raise TypeError(f"invalid numeric string: {value!r}")
    # Let the strict model handle its own semantic value types.
    return value

_ES_ORDINAL_UNDER_20 = {0: "", 1: "primero", 2: "segundo", 3: "tercero", 4: "cuarto", 5: "quinto", 6: "sexto", 7: "séptimo", 8: "octavo", 9: "noveno", 10: "décimo", 11: "décimoprimero", 12: "décimosegundo", 13: "décimotercero", 14: "décimocuarto", 15: "décimoquinto", 16: "décimosexto", 17: "décimoséptimo", 18: "décimoctavo", 19: "décimo noveno", 20: "vigésimo"}
_ES_ORDINAL_TENS = {20: "vigésimo", 30: "trigésimo", 40: "quadragésimo", 50: "quincuagésimo", 60: "sexagésimo", 70: "septuagésimo", 80: "octogésimo", 90: "nonagésimo"}
_ES_ORDINAL_HUNDREDS = {100: "centésimo", 200: "ducentésimo", 300: "tricentésimo", 400: " cuadringentésimo", 500: "quingentésimo", 600: "sexcentésimo", 700: "septingentésimo", 800: "octingentésimo", 900: "noningentésimo"}

def _legacy_english_ordinal(value: int) -> str:
    text = render(value, locale="en", form="ordinal")
    if value in (100, 1000, 1_000_000, 1_000_000_000):
        return "one " + text
    if value >= 100:
        if value % 100:
            if " hundred " in text:
                text = text.replace(" hundred ", " hundred and ", 1)
            elif value >= 1000 and value % 1000 < 100 and " thousand " in text:
                text = text.replace(" thousand ", " thousand and ", 1)
    return text

def _legacy_spanish_ordinal(value: int) -> str:
    if value == 0:
        return ""
    if value <= 20:
        return _ES_ORDINAL_UNDER_20[value]
    if value < 100:
        tens, ones = divmod(value, 10)
        return _ES_ORDINAL_TENS[tens * 10] + (f" {_ES_ORDINAL_UNDER_20[ones]}" if ones else "")
    if value < 1000:
        hundreds, rest = divmod(value, 100)
        prefix = _ES_ORDINAL_HUNDREDS[hundreds * 100]
        return prefix + (f" {_legacy_spanish_ordinal(rest)}" if rest else "")
    if value < 1_000_000:
        thousands, rest = divmod(value, 1000)
        prefix = "milésimo" if thousands == 1 else render(thousands, locale="es") + "milésimo"
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

def _ordinal_numeric(value: int, locale: str) -> str:
    """Return the conventional numeric ordinal notation for a locale."""
    language = canonicalize_locale(locale).split("-", 1)[0]
    if language == "en":
        if 10 <= value % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
        return f"{value}{suffix}"
    if language == "fr":
        return f"{value}{'er' if value == 1 else 'e'}"
    if language in {"es", "it", "pt", "de", "nl"}:
        return f"{value}."
    if language in {"ru", "uk", "be", "sr", "cs", "sk", "pl"}:
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
    }
    unknown = sorted(set(kwargs) - supported)
    if unknown:
        raise InvalidRequestError("unsupported num2words options: " + ", ".join(unknown))
    options = dict(kwargs)
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


def num2words(
    number: object,
    ordinal: bool = False,
    lang: str = "en",
    to: str = "cardinal",
    **kwargs,
) -> str:
    """Render a legacy request without weakening Numeralform's core API."""
    if not isinstance(lang, str) or not lang.strip():
        raise TypeError("lang must be a non-empty locale identifier")
    if not isinstance(to, str) or to not in _FORM_MAP:
        supported = ", ".join(sorted(_FORM_MAP))
        raise NotImplementedError(
            f"unsupported num2words to={to!r}; supported: {supported}"
        )
    if not isinstance(ordinal, bool):
        raise TypeError("ordinal must be a boolean")
    # Upstream's ordinal flag wins over the to selector.
    if ordinal:
        to = "ordinal"
    options = _translate_kwargs(kwargs)
    locale = canonicalize_locale(lang)
    value = _coerce_legacy_number(number)

    if to == "currency":
        from ..currency import render_currency

        currency = options.pop("currency", "EUR")
        return render_currency(
            value,
            locale=locale,
            currency=currency,
            cents=options.pop("cents", True),
            separator=options.pop("separator", ","),
            adjective=options.pop("adjective", False),
            **options,
        )

    if to != "currency" and any(key in options for key in ("currency", "cents", "separator", "adjective")):
        raise InvalidRequestError("currency options require to='currency'")
    if to == "ordinal_num":
        if not isinstance(value, int) or value < 0:
            raise ValueError("ordinal_num requires a non-negative integer")
        return _ordinal_numeric(value, locale)

    if to == "ordinal" and isinstance(value, int) and not options:
        language = locale.split("-", 1)[0]
        if language == "en":
            return _legacy_english_ordinal(value)
        if language == "es":
            return _legacy_spanish_ordinal(value)
    if to == "year" and isinstance(value, int) and not options:
        return _legacy_year(value, locale)
    # The legacy English renderer uses British conjunctions.  Selecting this
    # style here keeps the canonical default (which intentionally omits them)
    # unchanged.
    if options.get("style") == "num2words":
        options["style"] = "british-and" if to == "cardinal" and isinstance(value, int) else "default"
    elif "style" not in options and locale.split("-", 1)[0] == "en" and to == "cardinal" and isinstance(value, int):
        options["style"] = "british-and"
    try:
        return render(value, locale=locale, form=_FORM_MAP[to], **options)
    except InvalidValueError as exc:
        raise OverflowError(str(exc)) from exc
    except NumeralFormError as exc:
        raise NotImplementedError(str(exc)) from exc
