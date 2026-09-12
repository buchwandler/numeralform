"""Indonesian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class IndonesianRenderer(LexicalRenderer):
    locale = "id"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "id", tuple(CARDINALS["id"][i] for i in range(10)), ordinal_prefix="ke-"
    )
