"""Czech numeral renderer."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from ..model import NumeralForm, NumeralRequest, NumeralResult
from .base import validate_request

_UNDER_20 = (
    "nula",
    "jedna",
    "dva",
    "tři",
    "čtyři",
    "pět",
    "šest",
    "sedm",
    "osm",
    "devět",
    "deset",
    "jedenáct",
    "dvanáct",
    "třináct",
    "čtrnáct",
    "patnáct",
    "šestnáct",
    "sedmnáct",
    "osmnáct",
    "devatenáct",
)
_TENS = (
    "",
    "",
    "dvacet",
    "třicet",
    "čtyřicet",
    "padesát",
    "šedesát",
    "sedmdesát",
    "osmdesát",
    "devadesát",
)
_HUNDREDS = (
    "",
    "sto",
    "dvěstě",
    "třista",
    "čtyřista",
    "pětset",
    "šestset",
    "sedmset",
    "osmset",
    "devětset",
)
_SCALES = [(1_000_000, "milion"), (1_000, "tisíc")]
_MAX_CARDINAL = 999_999_999


class CzechRenderer:
    locale = "cs"

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        return LocaleCapabilities(
            profiles=(
                CapabilityProfile(
                    NumeralForm.CARDINAL,
                    domain=NumericDomain(maximum=_MAX_CARDINAL),
                ),
                CapabilityProfile(NumeralForm.DIGITS),
                CapabilityProfile(NumeralForm.YEAR),
            ),
            notes=(
                "Czech cardinals. Ordinals are not implemented (not required by consumer).",
            ),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        validate_request(request, self.capabilities())
        value = request.value
        if request.form is NumeralForm.DIGITS:
            text = self._digits(value)
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
                "Czech cardinal supports integers from -999999999 through 999999999"
            )
        if value < 0:
            return "mínus " + self._cardinal(-value)
        if value < 20:
            return _UNDER_20[value]
        if value < 100:
            tens, units = divmod(value, 10)
            return _TENS[tens] + (f" {_UNDER_20[units]}" if units else "")
        if value < 1_000:
            hundreds, remainder = divmod(value, 100)
            prefix = _HUNDREDS[hundreds]
            return prefix + (f" {self._cardinal(remainder)}" if remainder else "")
        if value < 1_000_000:
            thousands, remainder = divmod(value, 1_000)
            prefix = (
                "tisíc"
                if thousands == 1
                else f"{self._cardinal(thousands)} {self._scale_form(thousands, 'tisíc', 'tisíce', 'tisíc')}"
            )
            return prefix + (f" {self._cardinal(remainder)}" if remainder else "")
        millions, remainder = divmod(value, 1_000_000)
        prefix = f"{self._cardinal(millions)} {self._scale_form(millions, 'milion', 'miliony', 'milionů')}"
        return prefix + (f" {self._cardinal(remainder)}" if remainder else "")

    @staticmethod
    def _scale_form(value: int, one: str, few: str, many: str) -> str:
        if value % 100 in (11, 12, 13, 14):
            return many
        if value % 10 == 1:
            return one
        if value % 10 in (2, 3, 4):
            return few
        return many

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
