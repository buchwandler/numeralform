"""Compatibility locale inventory and renderer dispatch."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .zh import render_zh


@dataclass(frozen=True, slots=True)
class LegacyLocaleResolution:
    requested: str
    upstream_key: str
    numeralform_locale: str


@dataclass(frozen=True, slots=True)
class CompatLocale:
    resolution: LegacyLocaleResolution
    renderer: Callable[..., str] | None


LEGACY_CONVERTER_KEYS = frozenset(
    {
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
        "en_IN",
        "en_NG",
        "eo",
        "es",
        "es_CO",
        "es_CR",
        "es_GT",
        "es_NI",
        "es_VE",
        "fa",
        "fi",
        "fr",
        "fr_BE",
        "fr_CH",
        "fr_DZ",
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
        "pt_BR",
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
        "zh_CN",
        "zh_HK",
        "zh_TW",
    }
)

COMPAT_RENDERERS: dict[str, Callable[..., str]] = {
    "zh": render_zh,
}


def resolve_compat_locale(lang: str) -> CompatLocale:
    if not isinstance(lang, str) or not lang.strip():
        raise TypeError("lang must be a non-empty locale identifier")
    upstream_key = lang if lang in LEGACY_CONVERTER_KEYS else lang[:2]
    if upstream_key not in LEGACY_CONVERTER_KEYS:
        raise NotImplementedError()
    resolution = LegacyLocaleResolution(
        lang, upstream_key, upstream_key.replace("_", "-")
    )
    return CompatLocale(resolution, COMPAT_RENDERERS.get(upstream_key.split("_", 1)[0]))


def render_compat(
    locale: CompatLocale, form: str, value: object, options: dict[str, object]
) -> str:
    if locale.renderer is None:
        raise NotImplementedError()
    return locale.renderer(value, form=form, **options)
