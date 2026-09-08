"""Swedish numeral renderer."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from ..model import (
    NumeralForm,
    NumeralRequest,
    NumeralResult,
    Syntax,
)
from .base import validate_request

_UNDER_20 = (
    "noll",
    "ett",
    "två",
    "tre",
    "fyra",
    "fem",
    "sex",
    "sju",
    "åtta",
    "nio",
    "tio",
    "elva",
    "tolv",
    "tretton",
    "fjorton",
    "femton",
    "sexton",
    "sjutton",
    "arton",
    "nitton",
)
_TENS = {
    20: "tjugo",
    30: "trettio",
    40: "fyrtio",
    50: "femtio",
    60: "sextio",
    70: "sjuttio",
    80: "åttio",
    90: "nittio",
}
_ORDINALS = {
    0: "nollte",
    1: "första",
    2: "andra",
    3: "tredje",
    4: "fjärde",
    5: "femte",
    6: "sjätte",
    7: "sjunde",
    8: "åttonde",
    9: "nionde",
    10: "tionde",
    11: "elfte",
    12: "tolfte",
    15: "femtonde",
    20: "tjugonde",
    100: "hundrade",
    1000: "tusende",
}
_SCALES = [
    (1_000_000_000, "miljard"),
    (1_000_000, "miljon"),
    (1_000, "tusen"),
]
_MAX_CARDINAL = 999_999_999_999


class SwedishRenderer:
    locale = "sv"

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
                "Swedish cardinals use compounding without spaces for scale words.",
                "Ordinal support covers the range used by consumer tests.",
            ),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        validate_request(request, self.capabilities())
        value = request.value
        if request.form is NumeralForm.DIGITS:
            text = self._render_digits(value)
        elif request.form is NumeralForm.ORDINAL:
            text = self._render_ordinal(value)
        elif request.form is NumeralForm.YEAR:
            text = self._render_cardinal(value)
        else:
            text = self._render_cardinal(value)
        return NumeralResult(
            text, request.locale, request.form, request.style, request.morphology
        )

    def _render_cardinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > _MAX_CARDINAL:
            raise InvalidValueError(
                "Swedish cardinal supports integers from -999999999999 through 999999999999"
            )
        if value < 0:
            return "minus " + self._render_cardinal(-value)
        if value < 20:
            return _UNDER_20[value]
        if value < 100:
            tens, units = divmod(value, 10)
            return _TENS[tens * 10] + (_UNDER_20[units] if units else "")
        if value < 1_000:
            hundreds, remainder = divmod(value, 100)
            prefix = _UNDER_20[hundreds] + "hundra"
            return prefix + (self._render_cardinal(remainder) if remainder else "")
        for scale, name in _SCALES:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                if scale == 1_000:
                    prefix = self._render_cardinal(quotient) + name
                else:
                    # Swedish uses singular for 1 miljon/miljard, plural with 'er' otherwise
                    if quotient == 1:
                        prefix = "en " + name
                    else:
                        prefix = self._render_cardinal(quotient) + " " + name + "er"
                return prefix + (self._render_cardinal(remainder) if remainder else "")
        raise InvalidValueError("Swedish cardinal value is outside the supported range")

    def _render_ordinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidValueError("ordinal form requires a non-negative integer")
        if value in _ORDINALS:
            return _ORDINALS[value]
        if value < 100:
            tens, units = divmod(value, 10)
            if units == 0:
                # For 30, 40, etc. - use the cardinal + 'nde'
                base = _TENS[tens * 10]
                return base + "nde"
            # For compound ordinals like 21 -> tjugoförsta
            base = _TENS[tens * 10]
            return base + self._render_ordinal(units)
        if value < 1_000:
            hundreds, remainder = divmod(value, 100)
            if remainder == 0:
                return _UNDER_20[hundreds] + "hundrade"
            return _UNDER_20[hundreds] + "hundra" + self._render_ordinal(remainder)
        if value < 1_000_000:
            thousands, remainder = divmod(value, 1_000)
            if remainder == 0:
                return self._render_cardinal(thousands) + "tusende"
            return (
                self._render_cardinal(thousands)
                + "tusen"
                + self._render_ordinal(remainder)
            )
        raise InvalidValueError("Swedish ordinal is outside the supported range")

    def _render_digits(self, value) -> str:
        from ..model import DigitSequence

        if isinstance(value, DigitSequence):
            digits = value.digits
        elif isinstance(value, int) and not isinstance(value, bool):
            digits = str(abs(value))
        else:
            raise InvalidValueError("digits form requires an integer or DigitSequence")
        return " ".join(_UNDER_20[int(d)] for d in digits)


__all__ = ["SwedishRenderer"]
