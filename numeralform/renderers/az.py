"""Azerbaijani canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class AzerbaijaniRenderer(LexicalRenderer):
    locale = "az"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "az", tuple(CARDINALS["az"][i] for i in range(10)), ordinal_suffix="inci"
    )
