"""Bengali canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class BengaliRenderer(LexicalRenderer):
    locale = "bn"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "bn", tuple(CARDINALS["bn"][i] for i in range(10)), negative="ঋণাত্মক"
    )
