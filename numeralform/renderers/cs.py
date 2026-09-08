"""Czech numeral renderer."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities
from ..model import NumeralForm, NumeralRequest, NumeralResult, Syntax
from .base import validate_request

_UNDER_20 = (
    "nula", "jedna", "dva", "tři", "čtyři", "pět", "šest", "sedm", "osm", "devět",
    "deset", "jedenáct", "dvanáct", "třináct", "čtrnáct", "patnáct", "šestnáct",
    "sedmnáct", "osmnáct", "devatenáct",
)
_TENS = ("", "", "dvacet", "třicet", "čtyřicet", "padesát", "šedesát", "sedmdesát", "osmdesát", "devadesát")
_HUNDREDS = ("", "sto", "dvěstě", "třista", "čtyřista", "pětset", "šestset", "sedmset", "osmset", "devětset")
_SCALES = [(1_000_000, "milion"), (1_000, "tisíc")]
_MAX_CARDINAL = 999_999_999


class CzechRenderer:
    locale = "cs"

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        return LocaleCapabilities(
            profiles=(CapabilityProfile(NumeralForm.CARDINAL), CapabilityProfile(NumeralForm.DIGITS), CapabilityProfile(NumeralForm.YEAR)),
            notes=("Czech cardinals. Ordinals are not implemented (not required by consumer).",),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        validate_request(request, self.capabilities())
        value = request.value
        if request.form is NumeralForm.DIGITS:
            text = self._digits(value)
        else:
            text = self._cardinal(value)
        return NumeralResult(text, request.locale, request.form, request.style, request.morphology)

    def _cardinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > _MAX_CARDINAL:
            raise InvalidValueError("Czech cardinal supports integers from -999999999 through 999999999")
        if value < 0:
            return "mínus " + self._cardinal(-value)
        if value < 20:
            return _UNDER_20[value]
        if value < 100:
            tens, units = divmod(value, 10)
            return _TENS[tens] + (_UNDER_20[units] if units else "")
        if value < 1_000:
            hundreds, remainder = divmod(value, 100)
            return _HUNDREDS[hundreds] + (self._cardinal(remainder) if remainder else "")
        if value < 1_000_000:
            thousands, remainder = divmod(value, 1_000)
            if thousands == 1:
                prefix = "tisíc"
            else:
                prefix = self._cardinal(thousands) + " tisíc"
            return prefix + (" " + self._cardinal(remainder) if remainder else "")
        millions, remainder = divmod(value, 1_000_000)
        if millions == 1:
            prefix = "milion"
        else:
            prefix = self._cardinal(millions) + " milionů"
        return prefix + (" " + self._cardinal(remainder) if remainder else "")

    def _digits(self, value) -> str:
        from ..model import DigitSequence
        if isinstance(value, DigitSequence):
            digits = value.digits
        elif isinstance(value, int) and not isinstance(value, bool):
            digits = str(abs(value))
        else:
            raise InvalidValueError("digits form requires an integer or DigitSequence")
        return " ".join(_UNDER_20[int(d)] for d in digits)


__all__ = ["CzechRenderer"]
