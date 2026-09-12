"""Armenian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class ArmenianRenderer(LexicalRenderer):
    locale = "hy"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "hy", tuple(CARDINALS["hy"][i] for i in range(10)), negative="մինուս"
    )
