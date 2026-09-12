"""Romanian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class RomanianRenderer(LexicalRenderer):
    locale = "ro"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "ro", tuple(CARDINALS["ro"][i] for i in range(10)), ordinal_prefix="al "
    )
