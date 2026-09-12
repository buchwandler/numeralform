"""Slovenian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class SlovenianRenderer(LexicalRenderer):
    locale = "sl"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "sl", tuple(CARDINALS["sl"][i] for i in range(10)), negative="minus"
    )
