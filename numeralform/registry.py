"""Built-in locale registry and capability discovery."""

from __future__ import annotations

from .errors import UnsupportedLocaleError
from .locale import LocaleCapabilities, canonicalize_locale, fallback_chain
from .model import Morphology, NumeralForm, NumeralRequest, Syntax
from .renderers.base import LocaleRenderer
from .renderers.generic import GenericLocaleRenderer
from .renderers.ordinal import OrdinalNotationRenderer

_RENDERERS: dict[str, LocaleRenderer] = {}
_BUILTINS_INITIALIZED = False
_ORDINAL_NUMERIC_LANGUAGES = {
    "am",
    "ar",
    "az",
    "be",
    "bn",
    "ca",
    "ce",
    "cs",
    "cy",
    "da",
    "de",
    "en",
    "en-IN",
    "en-NG",
    "eo",
    "es",
    "es-CO",
    "es-CR",
    "es-GT",
    "es-NI",
    "es-VE",
    "fa",
    "fi",
    "fr",
    "fr-BE",
    "fr-CH",
    "fr-DZ",
    "he",
    "hi",
    "hu",
    "hy",
    "id",
    "is",
    "it",
    "ja",
    "kn",
    "ko",
    "kz",
    "lt",
    "lv",
    "mn",
    "nl",
    "no",
    "pl",
    "pt",
    "pt-BR",
    "pt-PT",
    "ro",
    "ru",
    "sk",
    "sl",
    "sr",
    "sv",
    "te",
    "tet",
    "tg",
    "th",
    "tr",
    "uk",
    "vi",
    "zh",
    "zh-CN",
    "zh-HK",
    "zh-TW",
}


def register_locale(
    locale: str, renderer: type[LocaleRenderer] | LocaleRenderer
) -> None:
    """Register or replace a process-local stateless locale renderer."""
    tag = canonicalize_locale(locale)
    instance = renderer() if isinstance(renderer, type) else renderer
    if tag.split("-", 1)[0] in _ORDINAL_NUMERIC_LANGUAGES:
        instance = OrdinalNotationRenderer(tag, instance)
    _RENDERERS[tag] = instance


def _ensure_builtins() -> None:
    global _BUILTINS_INITIALIZED
    if _BUILTINS_INITIALIZED:
        return

    # Set the guard before importing/registering so a custom pre-registration
    # cannot suppress built-in initialization and re-entrant lookups are safe.
    _BUILTINS_INITIALIZED = True
    from .renderers import (
        CzechRenderer,
        EnglishIndiaRenderer,
        EnglishRenderer,
        FinnishRenderer,
        FrenchBelgiumRenderer,
        FrenchRenderer,
        FrenchSwissRenderer,
        GermanRenderer,
        ItalianRenderer,
        JapaneseRenderer,
        KoreanRenderer,
        PortugueseRenderer,
        RussianRenderer,
        SpanishRenderer,
        SwedishRenderer,
        ThaiRenderer,
        VietnameseRenderer,
    )

    for locale, renderer in (
        ("cs", CzechRenderer),
        ("de", GermanRenderer),
        ("en", EnglishRenderer),
        ("fi", FinnishRenderer),
        ("es", SpanishRenderer),
        ("fr", FrenchRenderer),
        ("it", ItalianRenderer),
        ("ja", JapaneseRenderer),
        ("ko", KoreanRenderer),
        ("pt", PortugueseRenderer("pt-PT")),
        ("pt-BR", PortugueseRenderer),
        ("pt-PT", PortugueseRenderer("pt-PT")),
        ("ru", RussianRenderer),
        ("sv", SwedishRenderer),
        ("th", ThaiRenderer),
        ("vi", VietnameseRenderer),
    ):
        if locale not in _RENDERERS:
            register_locale(locale, renderer)
    regional = {
        "en-IN": EnglishIndiaRenderer,
        "en-NG": EnglishRenderer,
        "es-CO": SpanishRenderer,
        "es-CR": SpanishRenderer,
        "es-GT": SpanishRenderer,
        "es-NI": SpanishRenderer,
        "es-VE": SpanishRenderer,
        "fr-BE": FrenchBelgiumRenderer,
        "fr-CH": FrenchSwissRenderer,
        "fr-DZ": FrenchRenderer,
    }
    for locale in (
        "am",
        "ar",
        "az",
        "be",
        "bn",
        "ca",
        "ce",
        "cy",
        "da",
        "en-IN",
        "en-NG",
        "eo",
        "es-CO",
        "es-CR",
        "es-GT",
        "es-NI",
        "es-VE",
        "fa",
        "fr-BE",
        "fr-CH",
        "fr-DZ",
        "he",
        "hi",
        "hu",
        "hy",
        "id",
        "is",
        "kn",
        "kz",
        "lt",
        "lv",
        "mn",
        "nl",
        "no",
        "pl",
        "ro",
        "sk",
        "sl",
        "sr",
        "te",
        "tet",
        "tg",
        "tr",
        "uk",
        "zh",
        "zh-CN",
        "zh-HK",
        "zh-TW",
    ):
        if locale not in _RENDERERS:
            renderer = regional.get(locale, GenericLocaleRenderer(locale))
            register_locale(locale, renderer)


def locales() -> tuple[str, ...]:
    _ensure_builtins()
    return tuple(sorted(_RENDERERS))


def resolve_locale(locale: str) -> str:
    _ensure_builtins()
    requested = canonicalize_locale(locale)
    for candidate in fallback_chain(requested):
        if candidate in _RENDERERS:
            return candidate
    raise UnsupportedLocaleError(
        f"unsupported locale {locale!r}; available locales: {', '.join(locales())}"
    )


def resolve(locale: str) -> LocaleRenderer:
    _ensure_builtins()
    return _RENDERERS[resolve_locale(locale)]


def is_registered(locale: str) -> bool:
    """Return whether this exact canonical locale tag is registered."""
    _ensure_builtins()
    try:
        return canonicalize_locale(locale) in _RENDERERS
    except Exception:  # noqa: BLE001
        return False


def supports(
    locale: str,
    *,
    form: NumeralForm | str | None = None,
    syntax: Syntax | str | None = None,
    morphology: Morphology | dict | None = None,
    style: str | None = None,
    value: object | None = None,
) -> bool:
    """Return whether a locale can execute the requested capability surface."""
    try:
        renderer = resolve(locale)
        capabilities = renderer.capabilities()
        if form is None:
            return bool(capabilities.forms) and style in (None, *capabilities.styles)
        normalized_form = NumeralForm.coerce(form)
        if not any(
            profile.form is normalized_form for profile in capabilities.profiles
        ):
            return False
        from .model import DecimalNumber, DigitSequence, FractionNumber
        from .renderers.base import validate_request

        sample = value
        if sample is None:
            sample = {
                NumeralForm.DECIMAL: DecimalNumber("0", "0"),
                NumeralForm.FRACTION: FractionNumber(0, 1),
                NumeralForm.DIGITS: DigitSequence("0"),
            }.get(normalized_form, 0)
        request = NumeralRequest(
            sample,
            resolve_locale(locale),
            normalized_form,
            syntax or Syntax.STANDALONE,
            Morphology(**morphology)
            if isinstance(morphology, dict)
            else morphology or Morphology(),
            style,
        )
        validate_request(request, capabilities)
        if value is not None:
            renderer.render(request)
        return True
    except Exception:  # noqa: BLE001
        return False


def capabilities(locale: str) -> LocaleCapabilities:
    return resolve(locale).capabilities()
