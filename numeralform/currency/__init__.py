"""Decimal-safe locale-aware currency realization for the compatibility API."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_DOWN

from ..errors import InvalidRequestError, InvalidValueError


@dataclass(frozen=True, slots=True)
class MoneyAmount:
    major: int
    minor: int
    currency: str
    negative: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.major, bool) or not isinstance(self.major, int):
            raise InvalidValueError("money major unit must be an integer")
        if isinstance(self.minor, bool) or not isinstance(self.minor, int) or not 0 <= self.minor < 100:
            raise InvalidValueError("money minor unit must be an integer from 0 through 99")
        if not isinstance(self.currency, str) or len(self.currency) != 3:
            raise InvalidRequestError("currency must be a three-letter code")
        if not isinstance(self.negative, bool):
            raise InvalidRequestError("money negative must be a boolean")


@dataclass(frozen=True, slots=True)
class CurrencyRequest:
    amount: MoneyAmount
    locale: str
    cents: bool = True
    separator: str = ","
    adjective: bool = False


_CURRENCIES = {
    "EUR": {"en": ("euro", "euros", "cent", "cents"), "fr": ("euro", "euros", "centime", "centimes"), "es": ("euro", "euros", "céntimo", "céntimos"), "de": ("Euro", "Euro", "Cent", "Cent"), "it": ("euro", "euro", "centesimo", "centesimi"), "pt": ("euro", "euros", "cêntimo", "cêntimos"), "ru": ("евро", "евро", "цент", "цента"), "fi": ("euro", "euroa", "sentti", "senttiä")},
    "USD": {"en": ("dollar", "dollars", "cent", "cents"), "es": ("dólar", "dólares", "centavo", "centavos"), "fr": ("dollar", "dollars", "cent", "cents"), "ru": ("доллар", "доллара", "цент", "цента")},
    "GBP": {"en": ("pound", "pounds", "penny", "pence"), "fr": ("livre", "livres", "penny", "pence")},
    "RUB": {"ru": ("рубль", "рубля", "копейка", "копейки"), "en": ("ruble", "rubles", "kopeck", "kopecks")},
    "JPY": {"en": ("yen", "yen", "sen", "sen"), "ja": ("円", "円", "銭", "銭")},
    "CNY": {"en": ("yuan", "yuan", "fen", "fen"), "zh": ("元", "元", "分", "分")},
    "CAD": {"en": ("Canadian dollar", "Canadian dollars", "cent", "cents")},
    "AUD": {"en": ("Australian dollar", "Australian dollars", "cent", "cents")},
}


def _parse_amount(value) -> MoneyAmount:
    if isinstance(value, MoneyAmount):
        return value
    if isinstance(value, bool):
        raise TypeError("currency amount must be numeric")
    if isinstance(value, int):
        return MoneyAmount(value, 0, "EUR")
    from ..model import DecimalNumber
    if isinstance(value, DecimalNumber):
        integer = int(value.integer)
        minor = int((value.fraction + "00")[:2])
        return MoneyAmount(integer, minor, "EUR", value.negative)
    if isinstance(value, float):
        value = Decimal(str(value))
    if isinstance(value, str):
        try:
            value = Decimal(value.strip())
        except InvalidOperation as exc:
            raise TypeError("currency amount must be numeric") from exc
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise TypeError("currency amount must be finite")
        negative = value < 0
        absolute = abs(value)
        major = int(absolute.to_integral_value(rounding=ROUND_DOWN))
        minor = int(((absolute - major) * 100).to_integral_value(rounding=ROUND_DOWN))
        return MoneyAmount(major, minor, "EUR", negative)
    raise TypeError("currency amount must be numeric")


def _words(value: int, locale: str) -> str:
    from .. import render
    return render(value, locale=locale, style="british-and" if locale.split("-", 1)[0] == "en" else None)


def render_currency(value, *, locale: str = "en", currency: str = "EUR", cents: bool = True, separator: str = ",", adjective: bool = False, **kwargs) -> str:
    """Render a major/minor currency amount without binary arithmetic."""
    from ..locale import canonicalize_locale
    locale = canonicalize_locale(locale)
    code = currency.upper() if isinstance(currency, str) else currency
    if not isinstance(code, str) or len(code) != 3:
        raise InvalidRequestError("currency must be a three-letter code")
    amount = _parse_amount(value)
    amount = MoneyAmount(amount.major, amount.minor, code, amount.negative)
    language = locale.split("-", 1)[0]
    names = _CURRENCIES.get(code, {}).get(language) or _CURRENCIES.get(code, {}).get("en")
    if names is None:
        raise NotImplementedError(f"currency {code!r} is not implemented for locale {locale!r}")
    major_name = names[0] if amount.major == 1 else names[1]
    minor_name = names[2] if amount.minor == 1 else names[3]
    sign = "minus " if amount.negative and language == "en" else "menos " if amount.negative and language in {"es", "pt"} else "минус " if amount.negative and language == "ru" else ""
    text = f"{sign}{_words(amount.major, locale)} {major_name}"
    if cents:
        text += f"{separator} {_words(amount.minor, locale)} {minor_name}"
    return text


realize_currency = render_currency

__all__ = ["CurrencyRequest", "MoneyAmount", "realize_currency", "render_currency"]
