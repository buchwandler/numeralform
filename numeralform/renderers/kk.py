"""Kazakh canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class KazakhRenderer(LexicalRenderer):
    locale = "kk"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "kk", tuple(CARDINALS["kk"][i] for i in range(10)), negative="минус"
    )
