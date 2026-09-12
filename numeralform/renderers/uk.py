"""Ukrainian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class UkrainianRenderer(LexicalRenderer):
    locale = "uk"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "uk", tuple(CARDINALS["uk"][i] for i in range(10)), negative="мінус"
    )
