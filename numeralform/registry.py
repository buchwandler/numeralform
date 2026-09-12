"""Built-in locale registry and capability discovery."""

from __future__ import annotations

from typing import cast

from .errors import (
    InvalidRequestError,
    InvalidValueError,
    UnsupportedFormError,
    UnsupportedLocaleError,
    UnsupportedMorphologyError,
    UnsupportedStyleError,
)
from .locale import LocaleCapabilities, canonicalize_locale, fallback_chain
from .model import (
    Morphology,
    NumeralForm,
    NumeralRequest,
    NumericValue,
    Syntax,
    coerce_value,
)
from .renderers._shared import DecimalFallbackRenderer
from .renderers.base import LocaleRenderer
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
    "kk",
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
    if NumeralForm.DECIMAL not in instance.capabilities().forms:
        instance = DecimalFallbackRenderer(instance)
    if (
        tag.split("-", 1)[0] in _ORDINAL_NUMERIC_LANGUAGES
        and instance.capabilities().forms
    ):
        instance = OrdinalNotationRenderer(tag, instance)
    _RENDERERS[tag] = instance


def _ensure_builtins() -> None:
    global _BUILTINS_INITIALIZED
    if _BUILTINS_INITIALIZED:
        return
    # Set the guard before importing/registering so re-entrant lookups are safe.
    _BUILTINS_INITIALIZED = True
    from .renderers import (
        AmharicRenderer,
        ArabicRenderer,
        ArmenianRenderer,
        AzerbaijaniRenderer,
        BelarusianRenderer,
        BengaliRenderer,
        CatalanRenderer,
        ChechenRenderer,
        ChineseRegionalRenderer,
        ChineseRenderer,
        CzechRenderer,
        DanishRenderer,
        DutchRenderer,
        EnglishGBRenderer,
        EnglishIndiaRenderer,
        EnglishNigeriaRenderer,
        EnglishRenderer,
        EnglishUSRenderer,
        EsperantoRenderer,
        FinnishRenderer,
        FrenchBelgiumRenderer,
        FrenchRenderer,
        FrenchSwissRenderer,
        GermanRenderer,
        HebrewRenderer,
        HindiRenderer,
        HungarianRenderer,
        IcelandicRenderer,
        IndonesianRenderer,
        ItalianRenderer,
        JapaneseRenderer,
        KannadaRenderer,
        KazakhRenderer,
        KoreanRenderer,
        LatvianRenderer,
        LithuanianRenderer,
        MongolianRenderer,
        NorwegianRenderer,
        PersianRenderer,
        PolishRenderer,
        PortugueseRenderer,
        RomanianRenderer,
        RussianRenderer,
        SerbianRenderer,
        SlovakRenderer,
        SlovenianRenderer,
        SpanishRenderer,
        SwedishRenderer,
        TajikRenderer,
        TeluguRenderer,
        TetumRenderer,
        ThaiRenderer,
        TurkishRenderer,
        UkrainianRenderer,
        VietnameseRenderer,
        WelshRenderer,
    )

    base_renderers: dict[str, object] = {
        "am": AmharicRenderer,
        "ar": ArabicRenderer,
        "az": AzerbaijaniRenderer,
        "be": BelarusianRenderer,
        "bn": BengaliRenderer,
        "ca": CatalanRenderer,
        "ce": ChechenRenderer,
        "cs": CzechRenderer,
        "cy": WelshRenderer,
        "da": DanishRenderer,
        "de": GermanRenderer,
        "en": EnglishRenderer,
        "eo": EsperantoRenderer,
        "es": SpanishRenderer,
        "fa": PersianRenderer,
        "fi": FinnishRenderer,
        "fr": FrenchRenderer,
        "he": HebrewRenderer,
        "hi": HindiRenderer,
        "hu": HungarianRenderer,
        "hy": ArmenianRenderer,
        "id": IndonesianRenderer,
        "is": IcelandicRenderer,
        "it": ItalianRenderer,
        "ja": JapaneseRenderer,
        "kk": KazakhRenderer,
        "kn": KannadaRenderer,
        "ko": KoreanRenderer,
        "lt": LithuanianRenderer,
        "lv": LatvianRenderer,
        "mn": MongolianRenderer,
        "nl": DutchRenderer,
        "no": NorwegianRenderer,
        "pl": PolishRenderer,
        "pt": PortugueseRenderer("pt-PT"),
        "ro": RomanianRenderer,
        "ru": RussianRenderer,
        "sk": SlovakRenderer,
        "sl": SlovenianRenderer,
        "sr": SerbianRenderer,
        "sv": SwedishRenderer,
        "te": TeluguRenderer,
        "tet": TetumRenderer,
        "tg": TajikRenderer,
        "th": ThaiRenderer,
        "tr": TurkishRenderer,
        "uk": UkrainianRenderer,
        "vi": VietnameseRenderer,
        "zh": ChineseRenderer,
        "pt-BR": PortugueseRenderer,
        "pt-PT": PortugueseRenderer("pt-PT"),
    }
    regional_renderers: dict[str, object] = {
        "en-GB": EnglishGBRenderer,
        "en-IN": EnglishIndiaRenderer,
        "en-NG": EnglishNigeriaRenderer,
        "en-US": EnglishUSRenderer,
        "es-CO": SpanishRenderer,
        "es-CR": SpanishRenderer,
        "es-GT": SpanishRenderer,
        "es-MX": SpanishRenderer,
        "es-NI": SpanishRenderer,
        "es-VE": SpanishRenderer,
        "fr-BE": FrenchBelgiumRenderer,
        "fr-CH": FrenchSwissRenderer,
        "fr-DZ": FrenchRenderer,
        "zh-CN": ChineseRegionalRenderer("zh-CN"),
        "zh-HK": ChineseRegionalRenderer("zh-HK"),
        "zh-TW": ChineseRegionalRenderer("zh-TW"),
    }
    for locale, renderer in {**base_renderers, **regional_renderers}.items():
        if locale not in _RENDERERS:
            register_locale(
                locale, cast(type[LocaleRenderer] | LocaleRenderer, renderer)
            )


def registered_locales() -> tuple[str, ...]:
    _ensure_builtins()
    return tuple(sorted(_RENDERERS))


def known_locales() -> tuple[str, ...]:
    """Return all built-in and registered locale identifiers."""
    return registered_locales()


def locales() -> tuple[str, ...]:
    """Return locales with at least one reviewed canonical form."""
    _ensure_builtins()
    return tuple(
        sorted(
            tag for tag, renderer in _RENDERERS.items() if renderer.capabilities().forms
        )
    )


def resolve_locale(locale: str) -> str:
    _ensure_builtins()
    requested = canonicalize_locale(locale)
    for candidate in fallback_chain(requested):
        renderer = _RENDERERS.get(candidate)
        if renderer is not None and renderer.capabilities().forms:
            return candidate
    raise UnsupportedLocaleError(
        f"unsupported locale {locale!r}; available locales: {', '.join(locales())}"
    )


def resolve(locale: str) -> LocaleRenderer:
    _ensure_builtins()
    requested = canonicalize_locale(locale)
    for candidate in fallback_chain(requested):
        renderer = _RENDERERS.get(candidate)
        if renderer is not None:
            return renderer
    raise UnsupportedLocaleError(f"unsupported locale {locale!r}")


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
    form: NumeralForm | str = NumeralForm.CARDINAL,
    syntax: Syntax | str = Syntax.STANDALONE,
    morphology: Morphology | dict | None = None,
    style: str | None = None,
    value: object | None = None,
) -> bool:
    """Return whether a locale can execute the complete requested surface."""
    try:
        renderer = resolve(locale)
        locale_tag = canonicalize_locale(locale)
        capabilities = renderer.capabilities()
        normalized_form = NumeralForm.coerce(form)
        from .model import DecimalNumber, DigitSequence, FractionNumber
        from .renderers.base import validate_request

        sample: NumericValue = (
            coerce_value(value)
            if value is not None
            else cast(
                NumericValue,
                {
                    NumeralForm.DECIMAL: DecimalNumber("0", "0"),
                    NumeralForm.FRACTION: FractionNumber(0, 1),
                    NumeralForm.DIGITS: DigitSequence("0"),
                }.get(normalized_form, 0),
            )
        )
        request = NumeralRequest(
            sample,
            locale_tag,
            normalized_form,
            Syntax.coerce(syntax),
            Morphology(**morphology)
            if isinstance(morphology, dict)
            else morphology or Morphology(),
            style,
        )
        validate_request(request, capabilities)
        if value is not None:
            renderer.render(request)
        return True
    except (
        InvalidRequestError,
        InvalidValueError,
        UnsupportedLocaleError,
        UnsupportedFormError,
        UnsupportedMorphologyError,
        UnsupportedStyleError,
    ):
        return False


def capabilities(locale: str) -> LocaleCapabilities:
    return resolve(locale).capabilities()
