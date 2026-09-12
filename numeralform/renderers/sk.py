"""Slovak canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class SlovakRenderer(LexicalRenderer):
    locale = "sk"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "sk",
        tuple(CARDINALS["sk"][i] for i in range(10)),
        compound="",
        negative="mínus",
    )
