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


def require_int(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise InvalidValueError("value must be an integer")
    return value


class LocaleRenderer(Protocol):
    locale: str

    def capabilities(self) -> LocaleCapabilities: ...

    def render(self, request: NumeralRequest) -> NumeralResult: ...


def _feature_label(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _accepts(values, value) -> bool:
    return "*" in values or value in values


def validate_request(request: NumeralRequest, capabilities: LocaleCapabilities) -> None:
    """Validate generic semantic and exact capability constraints."""
    _validate_value_for_form(request.form, request.value)

    profiles = [
        profile for profile in capabilities.profiles if profile.form is request.form
    ]
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

    for profile in matching:
        if _profile_accepts_request(profile, request):
            _validate_domain(request, profile)
            return

    morphology = request.morphology
    if morphology.gender is not None:
        detail = f"gender {_feature_label(morphology.gender)}"
    elif morphology.case is not None:
        detail = f"case {_feature_label(morphology.case)}"
    elif morphology.animacy is not None:
        detail = f"animacy {_feature_label(morphology.animacy)}"
    elif morphology.grammatical_number is not None:
        detail = f"grammatical number {morphology.grammatical_number}"
    elif morphology.noun_class is not None:
        detail = f"noun class {morphology.noun_class}"
    elif morphology.definiteness is not None:
        detail = f"definiteness {morphology.definiteness}"
    elif morphology.state is not None:
        detail = f"state {morphology.state}"
    elif request.features.values:
        detail = "locale features " + ", ".join(sorted(request.features.values))
    else:
        detail = "requested morphology"
    raise UnsupportedMorphologyError(
        f"locale {request.locale!r} does not support {detail} for "
        f"{request.form.value}/{request.syntax.value}"
    )


def _profile_accepts_request(profile, request: NumeralRequest) -> bool:
    morphology = request.morphology
    return (
        (morphology.gender is None or morphology.gender in profile.genders)
        and (morphology.case is None or _accepts(profile.cases, morphology.case))
        and (
            morphology.animacy is None
            or _accepts(profile.animacies, _feature_label(morphology.animacy))
        )
        and (
            morphology.grammatical_number is None
            or _accepts(profile.grammatical_numbers, morphology.grammatical_number)
        )
        and (
            morphology.noun_class is None
            or _accepts(profile.noun_classes, morphology.noun_class)
        )
        and (
            morphology.definiteness is None
            or _accepts(profile.definitenesses, morphology.definiteness)
        )
        and (morphology.state is None or _accepts(profile.states, morphology.state))
        and _features_accept(profile.features, request.features)
    )


def _features_accept(specs, features) -> bool:
    by_name = {spec.name: spec for spec in specs}
    for name, value in features.items():
        spec = by_name.get(name)
        if spec is None:
            return False
        if spec.boolean:
            if not isinstance(value, bool):
                return False
        elif isinstance(value, str):
            if spec.values and value not in spec.values:
                return False
        elif isinstance(value, tuple):
            if spec.values and not all(item in spec.values for item in value):
                return False
        else:
            return False
    return True


def _validate_domain(request: NumeralRequest, profile) -> None:
    value = request.value
    domain = profile.domain
    if isinstance(value, int) and not isinstance(value, bool):
        if not domain.accepts_integer(value):
            raise InvalidValueError(
                f"{request.locale} {request.form.value} value {value} is outside its numeric domain"
            )
    elif isinstance(value, DecimalNumber):
        if not domain.decimals:
            # Existing renderers may still explicitly advertise DECIMAL while
            # using the default domain; only a true bounded profile rejects it.
            return
        integer = -int(value.integer) if value.negative else int(value.integer)
        if not domain.accepts_integer(integer):
            raise InvalidValueError(
                f"{request.locale} {request.form.value} integer part is outside its numeric domain"
            )
    elif isinstance(value, FractionNumber) and not domain.fractions:
        return


def _validate_value_for_form(form: NumeralForm, value: object) -> None:
    if form in (NumeralForm.CARDINAL, NumeralForm.YEAR):
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or (form is NumeralForm.YEAR and value < 0)
        ):
            raise InvalidValueError(f"{form.value} form requires an integer")
    elif form in (NumeralForm.ORDINAL, NumeralForm.ORDINAL_NUMERIC):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidValueError(
                f"{form.value} form requires a non-negative integer"
            )
    elif form is NumeralForm.DIGITS:
        if not (
            isinstance(value, DigitSequence)
            or (isinstance(value, int) and not isinstance(value, bool))
        ):
            raise InvalidValueError("digits form requires an integer or DigitSequence")
    elif form is NumeralForm.DECIMAL:
        if not isinstance(value, DecimalNumber):
            raise InvalidValueError("decimal form requires DecimalNumber or Decimal")
    elif form is NumeralForm.FRACTION and not isinstance(value, FractionNumber):
        raise InvalidValueError("fraction form requires FractionNumber or Fraction")
