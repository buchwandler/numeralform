"""Built-in locale registry and capability discovery."""

from __future__ import annotations

from .errors import UnsupportedLocaleError
from .locale import LocaleCapabilities, canonicalize_locale, fallback_chain
from .renderers.base import LocaleRenderer

_RENDERERS: dict[str, LocaleRenderer] = {}
_BUILTINS_INITIALIZED = False


def register_locale(
    locale: str, renderer: type[LocaleRenderer] | LocaleRenderer
) -> None:
    """Register or replace a process-local stateless locale renderer."""
    tag = canonicalize_locale(locale)
    instance = renderer() if isinstance(renderer, type) else renderer
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
        GermanRenderer,
        EnglishRenderer,
        FinnishRenderer,
        SpanishRenderer,
        FrenchRenderer,
        ItalianRenderer,
        JapaneseRenderer,
        KoreanRenderer,
        PortugueseRenderer,
        RussianRenderer,
        SwedishRenderer,
        ThaiRenderer,
        VietnameseRenderer,
        UnsupportedLocaleRenderer,
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
        "en-IN": EnglishRenderer,
        "en-NG": EnglishRenderer,
        "es-CO": SpanishRenderer,
        "es-CR": SpanishRenderer,
        "es-GT": SpanishRenderer,
        "es-NI": SpanishRenderer,
        "es-VE": SpanishRenderer,
        "fr-BE": FrenchRenderer,
        "fr-CH": FrenchRenderer,
        "fr-DZ": FrenchRenderer,
    }
    for locale in (
        "am", "ar", "az", "be", "bn", "ca", "ce", "cy", "da", "en-IN", "en-NG",
        "eo", "es-CO", "es-CR", "es-GT", "es-NI", "es-VE", "fa", "fr-BE",
        "fr-CH", "fr-DZ", "he", "hi", "hu", "hy", "id", "is", "kn", "kz", "lt",
        "lv", "mn", "nl", "no", "pl", "ro", "sk", "sl", "sr", "te", "tet",
        "tg", "tr", "uk", "zh", "zh-CN", "zh-HK", "zh-TW",
    ):
        if locale not in _RENDERERS:
            renderer = regional.get(locale, UnsupportedLocaleRenderer(locale))
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


def supports(locale: str) -> bool:
    try:
        resolve_locale(locale)
    except UnsupportedLocaleError:
        return False
    return True


def capabilities(locale: str) -> LocaleCapabilities:
    return resolve(locale).capabilities()
