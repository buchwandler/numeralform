"""Explicit canonical and num2words-compatibility currency realization."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from ..errors import InvalidRequestError, InvalidValueError


@dataclass(frozen=True, slots=True)
class MoneyAmount:
    major: int
    minor: int
    currency: str
    negative: bool = False
    minor_units: int = 2

    def __post_init__(self) -> None:
        if isinstance(self.major, bool) or not isinstance(self.major, int):
            raise InvalidValueError("money major unit must be an integer")
        if (
            isinstance(self.minor, bool)
            or not isinstance(self.minor, int)
            or self.minor < 0
            or self.minor >= 10**self.minor_units
        ):
            raise InvalidValueError("money minor unit is outside its currency scale")
        if not isinstance(self.currency, str) or len(self.currency) != 3:
            raise InvalidRequestError("currency must be a three-letter code")
        if not isinstance(self.negative, bool):
            raise InvalidRequestError("money negative must be a boolean")
        if (
            isinstance(self.minor_units, bool)
            or not isinstance(self.minor_units, int)
            or not 0 <= self.minor_units <= 6
        ):
            raise InvalidRequestError("money minor-unit scale must be between 0 and 6")


@dataclass(frozen=True, slots=True)
class CurrencyRequest:
    amount: MoneyAmount
    locale: str
    cents: bool = True
    separator: str | None = None

@dataclass(frozen=True, slots=True)
class CurrencyResult:
    text: str
    request: CurrencyRequest
    locale: str



@dataclass(frozen=True, slots=True)
class CurrencyUnitLexeme:
    forms: Mapping[str, str]
    gender: str | None = None
    attach: bool = False

    def form(self, category: str) -> str:
        return self.forms.get(category, self.forms.get("other", next(iter(self.forms.values()))))


@dataclass(frozen=True, slots=True)
class CurrencyLocalePolicy:
    major: CurrencyUnitLexeme
    minor: CurrencyUnitLexeme
    connector: str
    omit_zero_minor: bool = False

# The lexicon is deliberately data-driven.  Names not translated for a locale
# use the English form, while scale is independent metadata.
_CURRENCIES = {
    "EUR": {
        "en": ("euro", "euros", "cent", "cents"),
        "fr": ("euro", "euros", "centime", "centimes"),
        "es": ("euro", "euros", "céntimo", "céntimos"),
        "de": ("Euro", "Euro", "Cent", "Cent"),
        "it": ("euro", "euro", "centesimo", "centesimi"),
        "pt": ("euro", "euros", "cêntimo", "cêntimos"),
        "ru": ("евро", "евро", "цент", "цента"),
        "fi": ("euro", "euroa", "sentti", "senttiä"),
    },
    "USD": {
        "en": ("dollar", "dollars", "cent", "cents"),
        "es": ("dólar", "dólares", "centavo", "centavos"),
        "fr": ("dollar", "dollars", "cent", "cents"),
        "ru": ("доллар", "доллара", "цент", "цента"),
    },
    "GBP": {
        "en": ("pound", "pounds", "penny", "pence"),
        "fr": ("livre", "livres", "penny", "pence"),
    },
    "RUB": {
        "ru": ("рубль", "рубля", "копейка", "копейки"),
        "en": ("ruble", "rubles", "kopeck", "kopecks"),
    },
    "JPY": {"en": ("yen", "yen", "sen", "sen"), "ja": ("円", "円", "銭", "銭")},
    "CNY": {"en": ("yuan", "yuan", "fen", "fen"), "zh": ("元", "元", "分", "分")},
    "CAD": {"en": ("Canadian dollar", "Canadian dollars", "cent", "cents")},
    "AUD": {"en": ("Australian dollar", "Australian dollars", "cent", "cents")},
    "CHF": {
        "en": ("Swiss franc", "Swiss francs", "rappen", "rappen"),
        "fr": ("franc suisse", "francs suisses", "centime", "centimes"),
    },
    "INR": {"en": ("Indian rupee", "Indian rupees", "paise", "paise")},
    "KRW": {"en": ("won", "won", "jeon", "jeon"), "ko": ("원", "원", "전", "전")},
    "BRL": {
        "en": ("Brazilian real", "Brazilian reals", "centavo", "centavos"),
        "pt": ("real", "reais", "centavo", "centavos"),
    },
    "PLN": {"en": ("zloty", "zlotys", "grosz", "groszy")},
    "SEK": {"en": ("Swedish krona", "Swedish kronor", "öre", "öre")},
    "NOK": {"en": ("Norwegian krone", "Norwegian kroner", "øre", "øre")},
    "DKK": {"en": ("Danish krone", "Danish kroner", "øre", "øre")},
    "CZK": {"en": ("Czech koruna", "Czech korunas", "haléř", "haléřů")},
    "HUF": {"en": ("forint", "forints", "filler", "fillers")},
    "TRY": {"en": ("Turkish lira", "Turkish liras", "kuruş", "kuruş")},
    "UAH": {"en": ("hryvnia", "hryvnias", "kopiyka", "kopiykas")},
    "AED": {"en": ("dirham", "dirhams", "fils", "fils")},
    "SAR": {"en": ("riyal", "riyals", "halala", "halalas")},
    "KWD": {"en": ("Kuwaiti dinar", "Kuwaiti dinars", "fils", "fils")},
    "BHD": {"en": ("Bahraini dinar", "Bahraini dinars", "fils", "fils")},
}
_CONNECTORS = {
    "en": " and ",
    "de": " und ",
    "fr": " et ",
    "it": " e ",
    "pt": " e ",
    "fi": " ja ",
    "es": " con ",
    "ru": " и ",
    "cs": " a ",
    "ko": " ",
    "th": " และ ",
}

_CZECH_CURRENCIES = {
    "EUR": (("euro", "eura", "eur"), ("cent", "centy", "centů")),
    "USD": (("dolar", "dolary", "dolarů"), ("cent", "centy", "centů")),
    "GBP": (("libra", "libry", "liber"), ("pence", "pence", "pencí")),
    "JPY": (("jen", "yeny", "jenů"), ("sen", "sény", "senů")),
}
_RUSSIAN_CURRENCIES = {
    "EUR": (("евро", "евро", "евро"), ("цент", "цента", "центов")),
    "USD": (("доллар", "доллара", "долларов"), ("цент", "цента", "центов")),
    "RUB": (("рубль", "рубля", "рублей"), ("копейка", "копейки", "копеек")),
}
_SCRIPT_CURRENCIES = {
    "ko": {
        "EUR": ("유로", "센트"),
        "USD": ("달러", "센트"),
        "GBP": ("파운드", "펜스"),
        "JPY": ("엔", "전"),
        "KRW": ("원", "전"),
    },
    "th": {
        "EUR": ("ยูโร", "เซนต์"),
        "USD": ("ดอลลาร์", "เซนต์"),
        "GBP": ("ปอนด์", "เพนนี"),
        "JPY": ("เยน", "เซ็น"),
        "THB": ("บาท", "สตางค์"),
    },
}


def _plural_category(language: str, value: int) -> str:
    if language == "ru":
        value = abs(value)
        if value % 100 in (11, 12, 13, 14):
            return "many"
        if value % 10 == 1:
            return "one"
        if value % 10 in (2, 3, 4):
            return "few"
        return "many"
    if language == "cs":
        value = abs(value)
        if value == 1:
            return "one"
        if value % 10 in (2, 3, 4) and value % 100 not in (12, 13, 14):
            return "few"
        return "many"
    return "one" if abs(value) == 1 else "other"


def _currency_policy(code: str, language: str) -> CurrencyLocalePolicy:
    script_names = _SCRIPT_CURRENCIES.get(language, {}).get(code)
    if script_names is not None:
        major_name, minor_name = script_names
        return CurrencyLocalePolicy(
            CurrencyUnitLexeme({"one": major_name, "other": major_name}, attach=language == "th"),
            CurrencyUnitLexeme({"one": minor_name, "other": minor_name}, attach=language == "th"),
            _CONNECTORS[language],
        )
    if language == "ru" and code in _RUSSIAN_CURRENCIES:
        major, minor = _RUSSIAN_CURRENCIES[code]
        return CurrencyLocalePolicy(
            CurrencyUnitLexeme({"one": major[0], "few": major[1], "many": major[2]}),
            CurrencyUnitLexeme({"one": minor[0], "few": minor[1], "many": minor[2]}),
            _CONNECTORS[language],
        )
    if language == "cs" and code in _CZECH_CURRENCIES:
        major, minor = _CZECH_CURRENCIES[code]
        return CurrencyLocalePolicy(
            CurrencyUnitLexeme({"one": major[0], "few": major[1], "many": major[2]}),
            CurrencyUnitLexeme({"one": minor[0], "few": minor[1], "many": minor[2]}),
            _CONNECTORS[language],
        )
    names = _CURRENCIES.get(code, {}).get(language) or _CURRENCIES.get(code, {}).get("en")
    if names is None:
        raise NotImplementedError(f"currency {code!r} is not implemented for locale {language!r}")
    if language == "ru":
        major_forms = {"one": names[0], "few": names[1], "many": names[1]}
        minor_forms = {"one": names[2], "few": names[3], "many": names[3]}
    else:
        major_forms = {"one": names[0], "other": names[1]}
        minor_forms = {"one": names[2], "other": names[3]}
    gender = "masculine" if language == "es" else None
    return CurrencyLocalePolicy(
        CurrencyUnitLexeme(major_forms, gender=gender),
        CurrencyUnitLexeme(minor_forms, gender=gender),
        _CONNECTORS.get(language, ", "),
    )


_CURRENCY_MINOR_UNITS = {code: 2 for code in _CURRENCIES}
_CURRENCY_MINOR_UNITS.update({"JPY": 0, "KRW": 0, "KWD": 3, "BHD": 3})


def _currency_scale(code: str) -> int:
    try:
        return _CURRENCY_MINOR_UNITS[code]
    except KeyError as exc:
        raise NotImplementedError(f"currency {code!r} is not implemented") from exc


def _parse_amount(
    value, currency: str = "EUR", *, compatibility: str | None = None
) -> MoneyAmount:
    scale = _currency_scale(currency)
    unit = 10**scale
    if isinstance(value, MoneyAmount):
        return MoneyAmount(value.major, value.minor, currency, value.negative, scale)
    if isinstance(value, bool):
        raise TypeError("currency amount must be numeric")
    if isinstance(value, int):
        negative = value < 0
        absolute = abs(value)
        if compatibility == "num2words-0.5.14":
            return MoneyAmount(
                absolute // unit, absolute % unit, currency, negative, scale
            )
        return MoneyAmount(absolute, 0, currency, negative, scale)
    from ..model import DecimalNumber

    if isinstance(value, DecimalNumber):
        decimal = Decimal(
            ("-" if value.negative else "") + f"{value.integer}.{value.fraction}"
        )
    elif isinstance(value, float):
        decimal = Decimal(str(value))
    elif isinstance(value, str):
        try:
            decimal = Decimal(value.strip())
        except InvalidOperation as exc:
            raise TypeError("currency amount must be numeric") from exc
    elif isinstance(value, Decimal):
        decimal = value
    else:
        raise TypeError("currency amount must be numeric")
    if not decimal.is_finite():
        raise TypeError("currency amount must be finite")
    negative = decimal < 0
    quantizer = Decimal(1).scaleb(-scale)
    rounded = abs(decimal).quantize(quantizer, rounding=ROUND_HALF_UP)
    major = int(rounded)
    minor = int((rounded - major) * unit)
    return MoneyAmount(major, minor, currency, negative, scale)


def _words(value: int, locale: str, *, gender: str | None = None) -> str:
    from .. import render
    from ..model import Syntax

    language = locale.split("-", 1)[0]
    style = "british-and" if language == "en" else None
    kwargs = {"locale": locale, "style": style}
    if language == "es" and gender is not None:
        kwargs.update(syntax=Syntax.ATTRIBUTIVE, gender=gender)
    return render(value, **kwargs)

def render_currency(
    value,
    *,
    locale: str = "en",
    currency: str = "EUR",
    cents: bool = True,
    separator: str | None = None,
    compatibility: str | None = None,
) -> str:
    """Render a currency amount with locale-owned morphology and joining."""
    from ..registry import resolve_locale

    locale = resolve_locale(locale)
    if separator is not None and not isinstance(separator, str):
        raise TypeError("separator must be a string")
    code = currency.upper() if isinstance(currency, str) else currency
    if not isinstance(code, str) or len(code) != 3:
        raise InvalidRequestError("currency must be a three-letter code")
    amount = _parse_amount(value, code, compatibility=compatibility)
    language = locale.split("-", 1)[0]
    policy = _currency_policy(code, language)
    major_category = _plural_category(language, amount.major)
    major_name = policy.major.form(major_category)
    major_words = _words(amount.major, locale, gender=policy.major.gender)
    major_piece = f"{major_words}{major_name}" if policy.major.attach else f"{major_words} {major_name}"
    sign = (
        "minus "
        if amount.negative and language == "en"
        else "menos "
        if amount.negative and language in {"es", "pt"}
        else "минус "
        if amount.negative and language == "ru"
        else ""
    )
    text = sign + major_piece
    if amount.minor_units and not (policy.omit_zero_minor and amount.minor == 0):
        minor_category = _plural_category(language, amount.minor)
        minor_name = policy.minor.form(minor_category)
        minor_value = (
            _words(amount.minor, locale, gender=policy.minor.gender)
            if cents
            else f"{amount.minor:0{amount.minor_units}d}"
        )
        minor_piece = f"{minor_value}{minor_name}" if policy.minor.attach else f"{minor_value} {minor_name}"
        joiner = f"{separator} " if separator is not None else policy.connector
        text += joiner + minor_piece
    return text

def realize_currency(
    request_or_value: CurrencyRequest | MoneyAmount | object,
    *,
    locale: str = "en",
    currency: str = "EUR",
    cents: bool = True,
    separator: str | None = None,
) -> CurrencyResult:
    """Realize a currency request and return structured metadata."""
    if isinstance(request_or_value, CurrencyRequest):
        request = request_or_value
    else:
        amount = _parse_amount(request_or_value, currency)
        request = CurrencyRequest(amount, locale, cents, separator)
    text = render_currency(
        request.amount,
        locale=request.locale,
        currency=request.amount.currency,
        cents=request.cents,
        separator=request.separator,
    )
    from ..registry import resolve_locale

    return CurrencyResult(text, request, resolve_locale(request.locale))


__all__ = [
    "CurrencyLocalePolicy",
    "CurrencyRequest",
    "CurrencyResult",
    "CurrencyUnitLexeme",
    "MoneyAmount",
    "realize_currency",
    "render_currency",
]
