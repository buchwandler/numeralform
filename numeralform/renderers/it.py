"""Italian numeral renderer."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities
from ..model import NumeralForm, NumeralRequest, NumeralResult, Syntax
from .base import validate_request

_UNDER_20 = (
    "zero",
    "uno",
    "due",
    "tre",
    "quattro",
    "cinque",
    "sei",
    "sette",
    "otto",
    "nove",
    "dieci",
    "undici",
    "dodici",
    "tredici",
    "quattordici",
    "quindici",
    "sedici",
    "diciassette",
    "diciotto",
    "diciannove",
)
_TENS = (
    "",
    "",
    "venti",
    "trenta",
    "quaranta",
    "cinquanta",
    "sessanta",
    "settanta",
    "ottanta",
    "novanta",
)
_ORDINALS = {
    1: "primo",
    2: "secondo",
    3: "terzo",
    4: "quarto",
    5: "quinto",
    6: "sesto",
    7: "settimo",
    8: "ottavo",
    9: "nono",
    10: "decimo",
}
_SCALES = [(1_000_000_000, "miliardo"), (1_000_000, "milione"), (1_000, "mille")]
_MAX_CARDINAL = 999_999_999_999


class ItalianRenderer:
    locale = "it"

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        return LocaleCapabilities(
            profiles=(
                CapabilityProfile(NumeralForm.CARDINAL),
                CapabilityProfile(
                    NumeralForm.ORDINAL,
                    syntaxes=frozenset({Syntax.STANDALONE, Syntax.ORDINAL_ADJECTIVAL}),
                ),
                CapabilityProfile(NumeralForm.DIGITS),
                CapabilityProfile(NumeralForm.YEAR),
            ),
            notes=("Italian uses elision rules (ventuno, trentuno).",),
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
                "Italian cardinal supports integers up to 999999999999"
            )
        if value < 0:
            return "meno " + self._cardinal(-value)
        if value < 20:
            return _UNDER_20[value]
        if value < 100:
            tens, units = divmod(value, 10)
            base = _TENS[tens]
            if units in (1, 8):
                # Elision: ventuno, ventotto
                return base[:-1] + _UNDER_20[units]
            return base + (_UNDER_20[units] if units else "")
        if value < 1_000:
            hundreds, remainder = divmod(value, 100)
            if hundreds == 1:
                prefix = "cento"
            else:
                prefix = _UNDER_20[hundreds] + "cento"
            return prefix + (self._cardinal(remainder) if remainder else "")
        for scale, name in _SCALES:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                if scale == 1_000:
                    if quotient == 1:
                        prefix = "mille"
                    else:
                        prefix = self._cardinal(quotient) + "mila"
                else:
                    if quotient == 1:
                        prefix = f"un {name}"
                    else:
                        prefix = f"{self._cardinal(quotient)} {name}"
                return prefix + (f" {self._cardinal(remainder)}" if remainder else "")
        raise InvalidValueError("Italian cardinal value is outside the supported range")

    def _ordinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidValueError("ordinal form requires a non-negative integer")
        if value in _ORDINALS:
            return _ORDINALS[value]
        return self._cardinal(value) + "esimo"

    def _digits(self, value) -> str:
        from ..model import DigitSequence

        if isinstance(value, DigitSequence):
            digits = value.digits
        elif isinstance(value, int) and not isinstance(value, bool):
            digits = str(abs(value))
        else:
            raise InvalidValueError("digits form requires an integer or DigitSequence")
        return " ".join(_UNDER_20[int(d)] for d in digits)


__all__ = ["ItalianRenderer"]
