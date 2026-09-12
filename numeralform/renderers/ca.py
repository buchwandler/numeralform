"""Catalan canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class CatalanRenderer(LexicalRenderer):
    locale = "ca"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "ca", tuple(CARDINALS["ca"][i] for i in range(10)), ordinal_suffix="è"
    )
