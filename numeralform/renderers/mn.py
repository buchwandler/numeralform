"""Mongolian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class MongolianRenderer(LexicalRenderer):
    locale = "mn"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "mn", tuple(CARDINALS["mn"][i] for i in range(10)), negative="хасах"
    )
