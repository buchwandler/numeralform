"""Built-in locale registry and capability discovery."""

from __future__ import annotations

from typing import Type

from .errors import UnsupportedLocaleError
from .locale import LocaleCapabilities, canonicalize_locale, fallback_chain
from .renderers.base import LocaleRenderer

_RENDERER_TYPES: dict[str, type[LocaleRenderer]] = {}
_RENDERERS: dict[str, LocaleRenderer] = {}


def register_locale(
    locale: str, renderer: type[LocaleRenderer] | LocaleRenderer
) -> None:
    tag = canonicalize_locale(locale)
    if isinstance(renderer, type):
        instance = renderer()
    else:
        instance = renderer
    _RENDERERS[tag] = instance
    _RENDERER_TYPES[tag] = type(instance)


def _ensure_builtins() -> None:
    if _RENDERERS:
        return
    from .renderers import EnglishRenderer, RussianRenderer, SpanishRenderer

    register_locale("en", EnglishRenderer)
    register_locale("es", SpanishRenderer)
    register_locale("ru", RussianRenderer)


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
    return (
        _RENDERERS[resolve_locale(locale)]
        if _RENDERERS
        else _resolve_after_init(locale)
    )


def _resolve_after_init(locale: str) -> LocaleRenderer:
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
