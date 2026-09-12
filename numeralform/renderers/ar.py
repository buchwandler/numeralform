"""Arabic canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class ArabicRenderer(LexicalRenderer):
    locale = "ar"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "ar", tuple(CARDINALS["ar"][i] for i in range(10)), negative="سالب"
    )
