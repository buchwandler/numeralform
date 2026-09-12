"""Danish canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class DanishRenderer(LexicalRenderer):
    locale = "da"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data("da", tuple(CARDINALS["da"][i] for i in range(10)), compound="")
