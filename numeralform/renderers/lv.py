"""Latvian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class LatvianRenderer(LexicalRenderer):
    locale = "lv"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "lv", tuple(CARDINALS["lv"][i] for i in range(10)), negative="mīnuss"
    )
