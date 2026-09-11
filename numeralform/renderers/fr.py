"""French numeral renderer."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from ..model import NumeralForm, NumeralRequest, NumeralResult, Syntax
from .base import require_int, validate_request

_UNDER_20 = (
    "zéro",
    "un",
    "deux",
    "trois",
    "quatre",
    "cinq",
    "six",
    "sept",
    "huit",
    "neuf",
    "dix",
    "onze",
    "douze",
    "treize",
    "quatorze",
    "quinze",
    "seize",
    "dix-sept",
    "dix-huit",
    "dix-neuf",
)
_TENS = ("", "", "vingt", "trente", "quarante", "cinquante", "soixante")
_ORDINALS = {
    1: "premier",
    2: "deuxième",
    3: "troisième",
    4: "quatrième",
    5: "cinquième",
    6: "sixième",
    11: "onzième",
    12: "douzième",
    13: "treizième",
    14: "quatorzième",
    15: "quinzième",
    16: "seizième",
    17: "dix-septième",
    18: "dix-huitième",
    19: "dix-neuvième",
    7: "septième",
    8: "huitième",
    9: "neuvième",
    10: "dixième",
}
_SCALES = [(1_000_000_000, "milliard"), (1_000_000, "million"), (1_000, "mille")]
_MAX_CARDINAL = 999_999_999_999


class FrenchRenderer:
    locale = "fr"

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
                "French uses 70/80/90 system (soixante-dix, quatre-vingts, quatre-vingt-dix).",
            ),
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

    @staticmethod
    def _scale_quotient(value: str) -> str:
        return value[:-1] if value.endswith("quatre-vingts") else value

    def _cardinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > _MAX_CARDINAL:
            raise InvalidValueError(
                "French cardinal supports integers up to 999999999999"
            )
        if value < 0:
            return "moins " + self._cardinal(-value)
        if value < 20:
            return _UNDER_20[value]
        if value < 70:
            tens, units = divmod(value, 10)
            base = _TENS[tens]
            if units == 1:
                return f"{base} et un"
            return f"{base}-{_UNDER_20[units]}" if units else base
        if value < 80:
            if value == 70:
                return "soixante-dix"
            units = value - 60
            if units == 11:
                return "soixante et onze"
            return f"soixante-{_UNDER_20[units]}"
        if value < 100:
            if value == 80:
                return "quatre-vingts"
            units = value - 80
            return f"quatre-vingt-{_UNDER_20[units]}" if units else "quatre-vingts"
        if value < 1_000:
            hundreds, remainder = divmod(value, 100)
            if hundreds == 1:
                prefix = "cent"
            else:
                prefix = f"{self._cardinal(hundreds)} cent"
            if remainder == 0:
                return prefix + ("s" if hundreds > 1 else "")
            return f"{prefix} {self._cardinal(remainder)}"
        for scale, name in _SCALES:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                if scale == 1_000:
                    if quotient == 1:
                        prefix = "mille"
                    else:
                        prefix = (
                            f"{self._scale_quotient(self._cardinal(quotient))} mille"
                        )
                else:
                    if quotient == 1:
                        prefix = f"un {name}"
                    else:
                        prefix = (
                            f"{self._scale_quotient(self._cardinal(quotient))} {name}s"
                        )
                return prefix + (f" {self._cardinal(remainder)}" if remainder else "")
        raise InvalidValueError("French cardinal value is outside the supported range")

    def _ordinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidValueError("ordinal form requires a non-negative integer")
        if value in _ORDINALS:
            return _ORDINALS[value]
        if value < 100:
            tens, units = divmod(value, 10)
            if units:
                if units == 1:
                    full = self._cardinal(value)
                    return full.removesuffix("un") + "unième"
                prefix = self._cardinal(value - units)
                return f"{prefix}-{self._ordinal(units)}"
            cardinal = self._cardinal(value)
            return cardinal.removesuffix("s").removesuffix("e") + "ième"
        for scale, name in _SCALES:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                if remainder:
                    prefix = self._cardinal(value - remainder).removesuffix("s")
                    return f"{prefix} {self._ordinal(remainder)}"
                if scale == 1_000 and quotient == 1:
                    return "millième"
                cardinal = self._cardinal(value).removesuffix("s")
                return cardinal.removesuffix("e") + "ième"
        hundreds, remainder = divmod(value, 100)
        prefix = self._cardinal(value - remainder).removesuffix("s")
        return f"{prefix} {self._ordinal(remainder)}" if remainder else prefix + "ième"
    def _digits(self, value) -> str:
        from ..model import DigitSequence

        if isinstance(value, DigitSequence):
            digits = value.digits
        elif isinstance(value, int) and not isinstance(value, bool):
            digits = str(abs(value))
        else:
            raise InvalidValueError("digits form requires an integer or DigitSequence")
        return " ".join(_UNDER_20[int(d)] for d in digits)


__all__ = ["FrenchRenderer"]
