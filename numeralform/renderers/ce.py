"""Chechen canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data

_BARE_TENS = {"ткъа", "шовзткъа", "кхузткъа", "дезткъа"}


def _attributive(word: str) -> str:
    if word in _BARE_TENS:
        return word[:-1] + "е"
    if word.endswith("ъ"):
        return word[:-1]
    return word


class ChechenRenderer(LexicalRenderer):
    locale = "ce"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "ce", tuple(CARDINALS["ce"][i] for i in range(10)), negative="тӀехьара"
    )

    def _scale_prefix(self, scale: int, quotient: int) -> str:
        prefix = super()._scale_prefix(scale, quotient)
        if scale < 1_000:
            return prefix
        words = prefix.split(" ")
        if words:
            words[-1] = _attributive(words[-1])
        return " ".join(words)
