"""Dutch canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class DutchRenderer(LexicalRenderer):
    locale = "nl"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "nl", tuple(CARDINALS["nl"][i] for i in range(10)), compound="", negative="min"
    )
