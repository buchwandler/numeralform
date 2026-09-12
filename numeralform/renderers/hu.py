"""Hungarian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class HungarianRenderer(LexicalRenderer):
    locale = "hu"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "hu",
        tuple(CARDINALS["hu"][i] for i in range(10)),
        compound="",
        ordinal_suffix="adik",
    )
