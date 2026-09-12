"""Chechen canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class ChechenRenderer(LexicalRenderer):
    locale = "ce"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "ce", tuple(CARDINALS["ce"][i] for i in range(10)), negative="тӀехьара"
    )
