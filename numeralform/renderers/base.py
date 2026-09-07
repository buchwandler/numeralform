"""Renderer protocol and common request checks."""

from __future__ import annotations

from typing import Protocol

from ..errors import (
    InvalidValueError,
    UnsupportedFormError,
    UnsupportedMorphologyError,
    UnsupportedStyleError,
)
from ..locale import LocaleCapabilities
from ..model import (
    DecimalNumber,
    DigitSequence,
    FractionNumber,
    NumeralForm,
    NumeralRequest,
    NumeralResult,
)


class LocaleRenderer(Protocol):
    locale: str

    def capabilities(self) -> LocaleCapabilities: ...

    def render(self, request: NumeralRequest) -> NumeralResult: ...


def validate_request(request: NumeralRequest, capabilities: LocaleCapabilities) -> None:
    """Validate generic semantic and exact capability constraints."""
    _validate_value_for_form(request.form, request.value)

    profiles = [profile for profile in capabilities.profiles if profile.form is request.form]
    if not profiles:
        raise UnsupportedFormError(
            f"locale {request.locale!r} does not support {request.form.value} form"
        )

    style = request.style or "default"
    matching = [
        profile
        for profile in profiles
        if request.syntax in profile.syntaxes and style in profile.styles
    ]
    if not matching:
        if not any(request.syntax in profile.syntaxes for profile in profiles):
            raise UnsupportedMorphologyError(
                f"locale {request.locale!r} does not support {request.syntax.value} "
                f"syntax for {request.form.value} form"
            )
        raise UnsupportedStyleError(
            f"locale {request.locale!r} does not support style {request.style!r} "
            f"for {request.form.value} form"
        )

    morphology = request.morphology
    for profile in matching:
        if _profile_accepts_morphology(profile, morphology):
            return

    if morphology.gender is not None:
        detail = f"gender {morphology.gender.value}"
    elif morphology.case is not None:
        detail = f"case {morphology.case.value}"
    elif morphology.animacy is not None:
        detail = "animacy"
    elif morphology.grammatical_number is not None:
        detail = "grammatical number"
    elif morphology.noun_class is not None:
        detail = "noun class"
    else:
        detail = "requested morphology"
    raise UnsupportedMorphologyError(
        f"locale {request.locale!r} does not support {detail} for "
        f"{request.form.value}/{request.syntax.value}"
    )


def _profile_accepts_morphology(profile, morphology) -> bool:
    return (
        (morphology.gender is None or morphology.gender in profile.genders)
        and (morphology.case is None or morphology.case in profile.cases)
        and (morphology.animacy is None or profile.animacy)
        and (
            morphology.grammatical_number is None
            or profile.grammatical_number
        )
        and (morphology.noun_class is None or profile.noun_class)
    )


def _validate_value_for_form(form: NumeralForm, value: object) -> None:
    if form is NumeralForm.CARDINAL:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
    elif form is NumeralForm.ORDINAL:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidValueError("ordinal form requires a non-negative integer")
    elif form is NumeralForm.DIGITS:
        if not (
            isinstance(value, DigitSequence)
            or (isinstance(value, int) and not isinstance(value, bool))
        ):
            raise InvalidValueError("digits form requires an integer or DigitSequence")
    elif form is NumeralForm.DECIMAL:
        if not isinstance(value, DecimalNumber):
            raise InvalidValueError("decimal form requires DecimalNumber or Decimal")
    elif form is NumeralForm.FRACTION:
        if not isinstance(value, FractionNumber):
            raise InvalidValueError("fraction form requires FractionNumber or Fraction")
    elif form is NumeralForm.YEAR and (
        not isinstance(value, int) or isinstance(value, bool) or value < 0
    ):
        raise InvalidValueError("year form requires a non-negative integer")
