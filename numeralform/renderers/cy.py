"""Welsh canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class WelshRenderer(LexicalRenderer):
    locale = "cy"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data("cy", tuple(CARDINALS["cy"][i] for i in range(10)))
