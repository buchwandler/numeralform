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
    11: "elfte",
    12: "zwölfte",
    13: "dreizehnte",
    14: "vierzehnte",
    15: "fünfzehnte",
    16: "sechzehnte",
    17: "siebzehnte",
    18: "achtzehnte",
    19: "neunzehnte",
}
_SCALES = [
    (1_000_000_000_000, "Billion", "Billionen"),
    (1_000_000_000, "Milliarde", "Milliarden"),
    (1_000_000, "Million", "Millionen"),
    (1_000, "tausend", "tausend"),
    (100, "hundert", "hundert"),
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
            text = self._year(value)
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
            return _UNITS[value] if value > 1 else "eins"
        if value < 20:
            return _TEENS[value - 10]
        if value < 100:
            tens, units = divmod(value, 10)
            return _TENS[tens] if units == 0 else f"{_UNITS[units]}und{_TENS[tens]}"
        if value < 1_000:
            hundreds, remainder = divmod(value, 100)
            prefix = ("ein" if hundreds == 1 else _UNITS[hundreds]) + "hundert"
            return prefix + (self._cardinal(remainder) if remainder else "")
        for scale, singular, plural in _SCALES:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                if scale >= 1_000_000:
                    prefix = (
                        f"eine {singular}"
                        if quotient == 1
                        else f"{self._cardinal(quotient)} {plural}"
                    )
                    return prefix + (
                        f" {self._cardinal(remainder)}" if remainder else ""
                    )
                if scale == 1_000:
                    prefix = (
                        "eintausend"
                        if quotient == 1
                        else f"{self._cardinal(quotient)}tausend"
                    )
                    return prefix + (self._cardinal(remainder) if remainder else "")
        raise InvalidValueError("German cardinal value is outside the supported range")

    def _year(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidValueError("year form requires a non-negative integer")
        if 1100 <= value < 2000:
            century, remainder = divmod(value, 100)
            prefix = f"{self._cardinal(century)}hundert"
            return prefix + (self._cardinal(remainder) if remainder else "")
        return self._cardinal(value)

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
