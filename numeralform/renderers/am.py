"""Amharic canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class AmharicRenderer(LexicalRenderer):
    locale = "am"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "am", tuple(CARDINALS["am"][i] for i in range(10)), negative="አሉታዊ"
    )
