"""Explicit canonical and num2words-compatibility currency realization."""

from __future__ import annotations

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
    separator: str = ","


@dataclass(frozen=True, slots=True)
class CurrencyResult:
    text: str
    request: CurrencyRequest
    locale: str


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


def _words(value: int, locale: str) -> str:
    from .. import render

    style = "british-and" if locale.split("-", 1)[0] == "en" else None
    return render(value, locale=locale, style=style)


def render_currency(
    value,
    *,
    locale: str = "en",
    currency: str = "EUR",
    cents: bool = True,
    separator: str = ",",
    compatibility: str | None = None,
) -> str:
    """Render a currency amount with explicit canonical/legacy semantics."""
    from ..registry import resolve_locale

    locale = resolve_locale(locale)
    if not isinstance(separator, str):
        raise TypeError("separator must be a string")
    code = currency.upper() if isinstance(currency, str) else currency
    if not isinstance(code, str) or len(code) != 3:
        raise InvalidRequestError("currency must be a three-letter code")
    amount = _parse_amount(value, code, compatibility=compatibility)
    language = locale.split("-", 1)[0]
    names = _CURRENCIES.get(code, {}).get(language) or _CURRENCIES.get(code, {}).get(
        "en"
    )
    if names is None:
        raise NotImplementedError(
            f"currency {code!r} is not implemented for locale {locale!r}"
        )
    major_name = names[0] if amount.major == 1 else names[1]
    sign = (
        "minus "
        if amount.negative and language == "en"
        else "menos "
        if amount.negative and language in {"es", "pt"}
        else "минус "
        if amount.negative and language == "ru"
        else ""
    )
    text = f"{sign}{_words(amount.major, locale)} {major_name}"
    if amount.minor_units:
        minor_name = names[2] if amount.minor == 1 else names[3]
        if cents:
            text += f"{separator} {_words(amount.minor, locale)} {minor_name}"
        else:
            text += f"{separator} {amount.minor:0{amount.minor_units}d} {minor_name}"
    return text


def realize_currency(
    request_or_value: CurrencyRequest | MoneyAmount | object,
    *,
    locale: str = "en",
    currency: str = "EUR",
    cents: bool = True,
    separator: str = ",",
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
    "CurrencyRequest",
    "CurrencyResult",
    "MoneyAmount",
    "realize_currency",
    "render_currency",
]
