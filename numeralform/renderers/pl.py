"""Polish canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class PolishRenderer(LexicalRenderer):
    locale = "pl"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "pl", tuple(CARDINALS["pl"][i] for i in range(10)), negative="minus"
    )
