"""Telugu canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class TeluguRenderer(LexicalRenderer):
    locale = "te"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "te", tuple(CARDINALS["te"][i] for i in range(10)), negative="మైనస్"
    )
