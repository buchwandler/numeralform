"""Tajik canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class TajikRenderer(LexicalRenderer):
    locale = "tg"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "tg", tuple(CARDINALS["tg"][i] for i in range(10)), negative="манфӣ"
    )
