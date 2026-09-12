"""Kannada canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class KannadaRenderer(LexicalRenderer):
    locale = "kn"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "kn", tuple(CARDINALS["kn"][i] for i in range(10)), negative="ಮೈನಸ್"
    )
