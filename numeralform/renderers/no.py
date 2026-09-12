"""Norwegian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class NorwegianRenderer(LexicalRenderer):
    locale = "no"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data("no", tuple(CARDINALS["no"][i] for i in range(10)), compound="")
