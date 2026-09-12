"""Esperanto canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class EsperantoRenderer(LexicalRenderer):
    locale = "eo"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "eo", tuple(CARDINALS["eo"][i] for i in range(10)), ordinal_suffix="a"
    )
