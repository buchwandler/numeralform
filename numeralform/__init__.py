"""Locale-aware numeral morphology and spoken-number rendering."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from importlib.metadata import PackageNotFoundError, version
from typing import overload

from .currency import (
    CurrencyRequest,
    CurrencyResult,
    MoneyAmount,
    realize_currency,
    render_currency,
    supports_currency,
)
from .errors import (
    InvalidRequestError,
    InvalidValueError,
    NumeralFormError,
    UnsupportedFormError,
    UnsupportedLocaleError,
    UnsupportedMorphologyError,
    UnsupportedStyleError,
)
from .locale import (
    CapabilityProfile,
    FeatureSpec,
    Locale,
    LocaleCapabilities,
    NumericDomain,
    canonicalize_locale,
    fallback_chain,
    parse_locale,
)
from .model import (
    Animacy,
    Case,
    DecimalNumber,
    DigitSequence,
    FeatureScalar,
    FractionNumber,
    Gender,
    LocaleFeatures,
    Morphology,
    NumeralForm,
    NumeralRequest,
    NumeralResult,
    NumericInput,
    NumericValue,
    Syntax,
)
from .registry import (
    capabilities,
    is_registered,
    known_locales,
    locales,
    register_locale,
    registered_locales,
    resolve,
    resolve_locale,
    supports,
)

try:
    from ._version import __version__
except ImportError:
    try:
        __version__ = version("numeralform")
    except PackageNotFoundError:
        __version__ = "0+unknown"


@overload
def realize(request: NumeralRequest, /) -> NumeralResult: ...


@overload
def realize(
    value: NumericInput,
    /,
    *,
    locale: str,
    form: NumeralForm | str | None = None,
    syntax: Syntax | str = Syntax.STANDALONE,
    morphology: Morphology | None = None,
    style: str | None = None,
    features: LocaleFeatures | Mapping[str, FeatureScalar] | None = None,
    gender: Gender | str | None = None,
    case: Case | str | None = None,
    animacy: Animacy | str | None = None,
    grammatical_number: str | None = None,
    noun_class: str | None = None,
    definiteness: str | None = None,
    state: str | None = None,
) -> NumeralResult: ...


def realize(
    request: NumeralRequest | NumericInput,
    /,
    *,
    locale: str | None = None,
    form: NumeralForm | str | None = None,
    syntax: Syntax | str = Syntax.STANDALONE,
    morphology: Morphology | None = None,
    style: str | None = None,
    features: LocaleFeatures | Mapping[str, FeatureScalar] | None = None,
    gender: Gender | str | None = None,
    case: Case | str | None = None,
    animacy: Animacy | str | None = None,
    grammatical_number: str | None = None,
    noun_class: str | None = None,
    definiteness: str | None = None,
    state: str | None = None,
) -> NumeralResult:
    """Realize a numeric value or request and return complete metadata."""
    if isinstance(request, NumeralRequest):
        if (
            locale is not None
            or form is not None
            or syntax not in (Syntax.STANDALONE, Syntax.STANDALONE.value)
            or morphology is not None
            or style is not None
            or features is not None
            or any(
                option is not None
                for option in (
                    gender,
                    case,
                    animacy,
                    grammatical_number,
                    noun_class,
                    definiteness,
                    state,
                )
            )
        ):
            raise InvalidRequestError(
                "request objects cannot be combined with rendering keyword options"
            )
        normalized = replace(request, locale=canonicalize_locale(request.locale))
    else:
        if locale is None:
            raise InvalidRequestError("locale is required when rendering a value")
        if morphology is not None and any(
            option is not None
            for option in (
                gender,
                case,
                animacy,
                grammatical_number,
                noun_class,
                definiteness,
                state,
            )
        ):
            raise InvalidRequestError("use morphology or feature shortcuts, not both")
        morphology = morphology or Morphology(
            gender=gender,
            case=case,
            animacy=animacy,
            grammatical_number=grammatical_number,
            noun_class=noun_class,
            definiteness=definiteness,
            state=state,
        )
        if features is None:
            normalized_features = LocaleFeatures()
        elif isinstance(features, LocaleFeatures):
            normalized_features = features
        else:
            normalized_features = LocaleFeatures(features)
        normalized = NumeralRequest(
            request,
            canonicalize_locale(locale),
            form,  # type: ignore[arg-type]
            Syntax.coerce(syntax),
            morphology,
            style,
            normalized_features,
        )
    resolved_locale = resolve_locale(normalized.locale)
    result = resolve(normalized.locale).render(normalized)
    return replace(
        result,
        locale=resolved_locale,
        requested_locale=normalized.locale,
        form=normalized.form,
        syntax=normalized.syntax,
        morphology=normalized.morphology,
        style=result.style or "default",
        features=normalized.features,
    )


def render(
    value: NumericInput,
    *,
    locale: str,
    form: NumeralForm | str | None = None,
    syntax: Syntax | str = Syntax.STANDALONE,
    morphology: Morphology | None = None,
    style: str | None = None,
    features: LocaleFeatures | Mapping[str, FeatureScalar] | None = None,
    gender: Gender | str | None = None,
    case: Case | str | None = None,
    animacy: Animacy | str | None = None,
    grammatical_number: str | None = None,
    noun_class: str | None = None,
    definiteness: str | None = None,
    state: str | None = None,
) -> str:
    """Return the canonical spoken numeral text for a value."""
    return realize(
        value,
        locale=locale,
        form=form,
        syntax=syntax,
        morphology=morphology,
        style=style,
        features=features,
        gender=gender,
        case=case,
        animacy=animacy,
        grammatical_number=grammatical_number,
        noun_class=noun_class,
        definiteness=definiteness,
        state=state,
    ).text


def render_request(request: NumeralRequest) -> str:
    """Compatibility spelling for rendering a structured request."""
    return realize(request).text


__all__ = [
    "Animacy",
    "CapabilityProfile",
    "Case",
    "CurrencyRequest",
    "CurrencyResult",
    "DecimalNumber",
    "DigitSequence",
    "FeatureSpec",
    "FractionNumber",
    "Gender",
    "InvalidRequestError",
    "InvalidValueError",
    "Locale",
    "LocaleCapabilities",
    "LocaleFeatures",
    "MoneyAmount",
    "Morphology",
    "NumeralForm",
    "NumeralFormError",
    "NumeralRequest",
    "NumeralResult",
    "NumericDomain",
    "NumericInput",
    "NumericValue",
    "Syntax",
    "UnsupportedFormError",
    "UnsupportedLocaleError",
    "UnsupportedMorphologyError",
    "UnsupportedStyleError",
    "__version__",
    "canonicalize_locale",
    "capabilities",
    "fallback_chain",
    "is_registered",
    "known_locales",
    "locales",
    "parse_locale",
    "realize",
    "realize_currency",
    "register_locale",
    "registered_locales",
    "render",
    "render_currency",
    "render_request",
    "resolve",
    "resolve_locale",
    "supports",
    "supports_currency",
]
