"""Hindi canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class HindiRenderer(LexicalRenderer):
    locale = "hi"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "hi",
        tuple(CARDINALS["hi"][i] for i in range(10)),
        negative="माइनस",
        ordinal_suffix="वाँ",
    )
