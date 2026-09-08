"""Executable baseline renderer for locale registrations awaiting review.

The renderer preserves the typed Numeralform surface and deterministic error
behavior.  Locale-specific lexical and grammatical improvements can replace it
without changing registry or request contracts.
"""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from ..model import (
    DecimalNumber,
    DigitSequence,
    FractionNumber,
    NumeralForm,
    NumeralRequest,
    NumeralResult,
)
from .base import validate_request


class GenericLocaleRenderer:
    def __init__(self, locale: str):
        self.locale = locale

    def capabilities(self) -> LocaleCapabilities:
        domain = NumericDomain(decimals=True, fractions=True)
        return LocaleCapabilities(
            profiles=tuple(
                CapabilityProfile(form, domain=domain)
                for form in (
                    NumeralForm.CARDINAL,
                    NumeralForm.ORDINAL,
                    NumeralForm.DIGITS,
                    NumeralForm.DECIMAL,
                    NumeralForm.FRACTION,
                    NumeralForm.YEAR,
                )
            ),
            notes=(
                "Executable typed baseline; lexical and morphology review remains locale-specific.",
            ),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        validate_request(request, self.capabilities())
        value = request.value
        if request.form is NumeralForm.DIGITS:
            text = value.digits if isinstance(value, DigitSequence) else str(abs(value))
        elif request.form is NumeralForm.DECIMAL:
            if not isinstance(value, DecimalNumber):
                raise InvalidValueError("decimal form requires DecimalNumber")
            sign = "-" if value.negative else ""
            text = f"{sign}{value.integer}.{value.fraction}"
        elif request.form is NumeralForm.FRACTION:
            if not isinstance(value, FractionNumber):
                raise InvalidValueError("fraction form requires FractionNumber")
            text = f"{value.numerator}/{value.denominator}"
        elif request.form is NumeralForm.ORDINAL:
            text = f"{value}."
        else:
            text = str(value)
        return NumeralResult(
            text, request.locale, request.form, request.style, request.morphology
        )


__all__ = ["GenericLocaleRenderer"]
