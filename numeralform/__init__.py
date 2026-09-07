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
)
from .locale import (
    Locale,
    LocaleCapabilities,
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
    gender: Gender | str | None = None,
    case: Case | str | None = None,
    animacy: Animacy | str | None = None,
    grammatical_number: str | None = None,
    noun_class: str | None = None,
) -> NumeralResult:
    """Realize a numeric value and return text with request metadata.

    Pass a :class:`NumeralRequest` for the structured API, or pass a value with
    the same keyword options accepted by :func:`render`.
    """
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
                )
            )
            or style is not None
            or form != NumeralForm.CARDINAL
            or syntax != Syntax.STANDALONE
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
            for option in (gender, case, animacy, grammatical_number, noun_class)
        ):
            raise InvalidRequestError("use morphology or feature shortcuts, not both")
        morphology = morphology or Morphology(
            gender=gender,
            case=case,
            animacy=animacy,
            grammatical_number=grammatical_number,
            noun_class=noun_class,
        )
        normalized = NumeralRequest(
            request, canonicalize_locale(locale), form, syntax, morphology, style
        )
    renderer = resolve(normalized.locale)
    return renderer.render(normalized)


def render(value: object, *, locale: str, **options) -> str:
    """Return the canonical spoken numeral text for a value."""
    return realize(value, locale=locale, **options).text


def render_request(request: NumeralRequest) -> str:
    """Compatibility spelling for rendering a structured request."""
    return realize(request).text


__all__ = [
    "Animacy",
    "Case",
    "DecimalNumber",
    "DigitSequence",
    "FractionNumber",
    "Gender",
    "InvalidRequestError",
    "InvalidValueError",
    "Locale",
    "LocaleCapabilities",
    "Morphology",
    "NumeralForm",
    "NumeralFormError",
    "NumeralRequest",
    "NumeralResult",
    "NumericValue",
    "Syntax",
    "UnsupportedFormError",
    "UnsupportedLocaleError",
    "UnsupportedMorphologyError",
    "capabilities",
    "canonicalize_locale",
    "fallback_chain",
    "locales",
    "parse_locale",
    "realize",
    "register_locale",
    "render",
    "render_request",
    "resolve",
    "resolve_locale",
    "supports",
    "__version__",
]
