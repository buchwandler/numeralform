"""Belarusian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class BelarusianRenderer(LexicalRenderer):
    locale = "be"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "be", tuple(CARDINALS["be"][i] for i in range(10)), negative="мінус"
    )
