"""Serbian canonical numeral renderer using Cyrillic-independent Latin policy."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class SerbianRenderer(LexicalRenderer):
    locale = "sr"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "sr", tuple(CARDINALS["sr"][i] for i in range(10)), negative="minus"
    )
