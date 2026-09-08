"""Locale-aware numeral morphology and spoken-number rendering."""

from __future__ import annotations

from dataclasses import replace
from importlib.metadata import PackageNotFoundError, version

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
    FractionNumber,
    Gender,
    LocaleFeatures,
    Morphology,
    NumeralForm,
    NumeralRequest,
    NumeralResult,
    NumericValue,
    Syntax,
)
from .registry import (
    capabilities,
    locales,
    register_locale,
    resolve,
    resolve_locale,
    supports,
)
from .currency import CurrencyRequest, MoneyAmount, realize_currency, render_currency

try:
    from ._version import __version__
except ImportError:
    try:
        __version__ = version("numeralform")
    except PackageNotFoundError:
        __version__ = "0+unknown"


def realize(
    request: NumeralRequest | object,
    *,
    locale: str | None = None,
    form: NumeralForm | str = NumeralForm.CARDINAL,
    syntax: Syntax | str = Syntax.STANDALONE,
    morphology: Morphology | None = None,
    style: str | None = None,
    features: LocaleFeatures | dict | None = None,
    gender: Gender | str | None = None,
    case: Case | str | None = None,
    animacy: Animacy | str | None = None,
    grammatical_number: str | None = None,
    noun_class: str | None = None,
    definiteness: str | None = None,
    state: str | None = None,
) -> NumeralResult:
    """Realize a numeric value and return text with request metadata."""
    if isinstance(request, NumeralRequest):
        if (
            any(
                option is not None
                for option in (
                    locale,
                    morphology,
                    gender,
                    case,
                    animacy,
                    grammatical_number,
                    noun_class,
                    definiteness,
                    state,
                    features,
                )
            )
            or style is not None
            or form != NumeralForm.CARDINAL
            or syntax != Syntax.STANDALONE
        ):
            raise InvalidRequestError("request objects cannot be combined with rendering keyword options")
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
        normalized = NumeralRequest(
            request,
            canonicalize_locale(locale),
            form,
            syntax,
            morphology,
            style,
            LocaleFeatures(features or {}),
        )
    renderer = resolve(normalized.locale)
    if normalized.form is NumeralForm.ORDINAL_NUMERIC:
        ordinal_result = renderer.render(replace(normalized, form=NumeralForm.ORDINAL))
        number = normalized.value
        language = normalized.locale.split("-", 1)[0]
        if language == "en":
            suffix = "th" if 10 <= number % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
            text = f"{number}{suffix}"
        elif language == "fr":
            text = f"{number}{'er' if number == 1 else 'e'}"
        elif language in {"ja", "zh"}:
            text = f"第{number}"
        else:
            text = f"{number}."
        return NumeralResult(text, ordinal_result.locale, NumeralForm.ORDINAL_NUMERIC, normalized.style, normalized.morphology)
    return renderer.render(normalized)


def render(value: object, *, locale: str, **options) -> str:
    """Return the canonical spoken numeral text for a value."""
    return realize(value, locale=locale, **options).text


def render_request(request: NumeralRequest) -> str:
    """Compatibility spelling for rendering a structured request."""
    return realize(request).text


__all__ = [
    "Animacy",
    "CapabilityProfile",
    "Case",
    "DecimalNumber",
    "DigitSequence",
    "FeatureSpec",
    "CurrencyRequest",
    "FractionNumber",
    "Gender",
    "MoneyAmount",
    "InvalidRequestError",
    "InvalidValueError",
    "Locale",
    "LocaleCapabilities",
    "LocaleFeatures",
    "Morphology",
    "NumeralForm",
    "NumeralFormError",
    "NumeralRequest",
    "NumeralResult",
    "NumericDomain",
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
    "locales",
    "parse_locale",
    "realize",
    "register_locale",
    "render",
    "render_request",
    "realize_currency",
    "render_currency",
    "resolve",
    "resolve_locale",
    "supports",
]
