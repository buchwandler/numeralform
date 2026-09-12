"""Lithuanian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class LithuanianRenderer(LexicalRenderer):
    locale = "lt"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "lt", tuple(CARDINALS["lt"][i] for i in range(10)), negative="minus"
    )
