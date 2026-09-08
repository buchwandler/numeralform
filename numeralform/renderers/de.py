"""German numeral renderer."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from ..model import NumeralForm, NumeralRequest, NumeralResult, Syntax
from .base import validate_request

_UNITS = (
    "null",
    "ein",
    "zwei",
    "drei",
    "vier",
    "fünf",
    "sechs",
    "sieben",
    "acht",
    "neun",
)
_TEENS = (
    "zehn",
    "elf",
    "zwölf",
    "dreizehn",
    "vierzehn",
    "fünfzehn",
    "sechzehn",
    "siebzehn",
    "achtzehn",
    "neunzehn",
)
_TENS = (
    "",
    "",
    "zwanzig",
    "dreißig",
    "vierzig",
    "fünfzig",
    "sechzig",
    "siebzig",
    "achtzig",
    "neunzig",
)
_ORDINALS = {
    0: "nullte",
    1: "erste",
    2: "zweite",
    3: "dritte",
    4: "vierte",
    5: "fünfte",
    6: "sechste",
    7: "siebte",
    8: "achte",
    9: "neunte",
    10: "zehnte",
}
_SCALES = [
    (1_000_000_000_000, "Billion"),
    (1_000_000_000, "Milliarde"),
    (1_000_000, "Million"),
    (1_000, "tausend"),
    (100, "hundert"),
]
_MAX_CARDINAL = 999_999_999_999


class GermanRenderer:
    locale = "de"

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        return LocaleCapabilities(
            profiles=(
                CapabilityProfile(
                    NumeralForm.CARDINAL,
                    domain=NumericDomain(maximum=_MAX_CARDINAL),
                ),
                CapabilityProfile(
                    NumeralForm.ORDINAL,
                    syntaxes=frozenset({Syntax.STANDALONE, Syntax.ORDINAL_ADJECTIVAL}),
                ),
                CapabilityProfile(NumeralForm.DIGITS),
                CapabilityProfile(NumeralForm.YEAR),
            ),
            notes=(
                "German uses unit/tens inversion (einundzwanzig).",
                "Scale words capitalize (Million, Milliarde).",
            ),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        validate_request(request, self.capabilities())
        value = request.value
        if request.form is NumeralForm.DIGITS:
            text = self._digits(value)
        elif request.form is NumeralForm.ORDINAL:
            text = self._ordinal(value)
        elif request.form is NumeralForm.YEAR:
            text = self._cardinal(value)
        else:
            text = self._cardinal(value)
        return NumeralResult(
            text, request.locale, request.form, request.style, request.morphology
        )

    def _cardinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > _MAX_CARDINAL:
            raise InvalidValueError(
                "German cardinal supports integers up to 999999999999"
            )
        if value < 0:
            return "minus " + self._cardinal(-value)
        if value == 0:
            return "null"
        if value < 10:
            return _UNITS[value] if value > 1 else ("eins" if value == 1 else "null")
        if value < 20:
            return _TEENS[value - 10]
        if value < 100:
            tens, units = divmod(value, 10)
            if units == 0:
                return _TENS[tens]
            return f"{_UNITS[units]}und{_TENS[tens]}"
        if value < 1_000:
            hundreds, remainder = divmod(value, 100)
            prefix = ("ein" if hundreds == 1 else _UNITS[hundreds]) + "hundert"
            return prefix + (self._cardinal(remainder) if remainder else "")
        for scale, name in _SCALES:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                if scale >= 1_000_000:
                    if quotient == 1:
                        prefix = f"eine {name}"
                    else:
                        prefix = f"{self._cardinal(quotient)} {name}"
                    # Add 'n' for plural Milliarden
                    if scale == 1_000_000_000 and quotient > 1:
                        prefix += "n"
                elif scale == 1_000:
                    prefix = (
                        "ein" if quotient == 1 else self._cardinal(quotient)
                    ) + name
                else:
                    prefix = ("ein" if quotient == 1 else _UNITS[quotient]) + name
                return prefix + (self._cardinal(remainder) if remainder else "")
        raise InvalidValueError("German cardinal value is outside the supported range")

    def _ordinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidValueError("ordinal form requires a non-negative integer")
        if value in _ORDINALS:
            return _ORDINALS[value]
        # German ordinals: cardinal + "ste" or "te"
        cardinal = self._cardinal(value)
        if cardinal.endswith("e"):
            return cardinal + "te"
        return cardinal + "ste"

    def _digits(self, value) -> str:
        from ..model import DigitSequence

        if isinstance(value, DigitSequence):
            digits = value.digits
        elif isinstance(value, int) and not isinstance(value, bool):
            digits = str(abs(value))
        else:
            raise InvalidValueError("digits form requires an integer or DigitSequence")
        digit_words = (
            "null",
            "eins",
            "zwei",
            "drei",
            "vier",
            "fünf",
            "sechs",
            "sieben",
            "acht",
            "neun",
        )
        return " ".join(digit_words[int(d)] for d in digits)


__all__ = ["GermanRenderer"]
