from __future__ import annotations

from numeralform import (
    DecimalNumber,
    DigitSequence,
    locales,
    render,
    resolve_locale,
    supports,
)

BASES = [
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
    "eo",
    "es",
    "fa",
    "fi",
    "fr",
    "he",
    "hi",
    "hu",
    "hy",
    "id",
    "is",
    "it",
    "ja",
    "kk",
    "kn",
    "ko",
    "lt",
    "lv",
    "mn",
    "nl",
    "no",
    "pl",
    "pt",
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
]
REGIONAL = [
    "en-GB",
    "en-IN",
    "en-NG",
    "en-US",
    "es-CO",
    "es-CR",
    "es-GT",
    "es-MX",
    "es-NI",
    "es-VE",
    "fr-BE",
    "fr-CH",
    "fr-DZ",
    "pt-BR",
    "zh-CN",
    "zh-HK",
    "zh-TW",
]


for locale in BASES:
    assert locale in locales(), locale
    assert supports(locale, form="cardinal", value=42), locale
    assert render(42, locale=locale), locale
    assert render(DigitSequence("0042"), locale=locale), locale
    assert supports(locale, form="decimal", value=DecimalNumber("1", "20")), locale
    assert render(DecimalNumber("1", "20"), locale=locale), locale
    assert render(2024, locale=locale, form="year"), locale

for locale in REGIONAL:
    assert resolve_locale(locale) == locale, locale
    assert render(42, locale=locale), locale

assert render(3, locale="ko", form="ordinal") == "세 번째"
assert render(3, locale="ko", form="ordinal_num") == "3번째"
print(f"validated {len(BASES)} bases and {len(REGIONAL)} regional locales")
