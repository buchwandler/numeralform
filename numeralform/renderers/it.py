"""Italian numeral renderer."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from ..model import NumeralForm, NumeralRequest, NumeralResult, Syntax
from .base import require_int, validate_request

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
_SCALES = [
    (1_000_000_000, "miliardo", "miliardi"),
    (1_000_000, "milione", "milioni"),
    (1_000, "mille", "mila"),
]
_MAX_CARDINAL = 999_999_999_999


_ITALIAN_ORDINAL_SUFFIXES = (
    ("tré", "treesimo"),
    ("tre", "treesimo"),
    ("uno", "unesimo"),
    ("due", "duesimo"),
    ("quattro", "quattresimo"),
    ("cinque", "cinquesimo"),
    ("sei", "seiesimo"),
    ("sette", "settesimo"),
    ("otto", "ottesimo"),
    ("nove", "novesimo"),
 )


def _ordinalize_italian_cardinal(text: str) -> str:
    for suffix, ordinal_suffix in _ITALIAN_ORDINAL_SUFFIXES:
        if text.endswith(suffix):
            return text.removesuffix(suffix) + ordinal_suffix
    return text.rstrip("aeiou") + "esimo"


class ItalianRenderer:
    locale = "it"

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
            notes=("Italian uses elision rules (ventuno, trentuno).",),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        validate_request(request, self.capabilities())
        value = request.value
        if request.form is NumeralForm.DIGITS:
            text = self._digits(value)
        elif request.form is NumeralForm.ORDINAL:
            text = self._ordinal(require_int(value))
        elif request.form is NumeralForm.YEAR:
            text = self._cardinal(require_int(value))
        else:
            text = self._cardinal(require_int(value))
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
        if value % 10 == 3:
            return self._cardinal(value - 3) + "tré"
        if value < 100:
            tens, units = divmod(value, 10)
            base = _TENS[tens]
            if units in (1, 8):
                return base[:-1] + _UNDER_20[units]
            return base + (_UNDER_20[units] if units else "")
        if value < 1_000:
            hundreds, remainder = divmod(value, 100)
            prefix = "cento" if hundreds == 1 else _UNDER_20[hundreds] + "cento"
            return prefix + (self._cardinal(remainder) if remainder else "")
        for scale, singular, plural in _SCALES:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                if scale == 1_000:
                    prefix = (
                        "mille" if quotient == 1 else self._cardinal(quotient) + "mila"
                    )
                    return prefix + (self._cardinal(remainder) if remainder else "")
                scale_name = singular if quotient == 1 else plural
                prefix = (
                    f"un {scale_name}"
                    if quotient == 1
                    else f"{self._cardinal(quotient)} {scale_name}"
                )
                return prefix + (f" e {self._cardinal(remainder)}" if remainder else "")
        raise InvalidValueError("Italian cardinal value is outside the supported range")

    def _ordinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidValueError("ordinal form requires a non-negative integer")
        if value in _ORDINALS:
            return _ORDINALS[value]
        cardinal = self._cardinal(value)
        if value < 100:
            return _ordinalize_italian_cardinal(cardinal)
        for scale, _singular, _plural in _SCALES:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                if remainder:
                    return self._cardinal(value - remainder) + self._ordinal(remainder)
                break
        return _ordinalize_italian_cardinal(cardinal)

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
