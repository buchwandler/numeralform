"""Persian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class PersianRenderer(LexicalRenderer):
    locale = "fa"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "fa",
        tuple(CARDINALS["fa"][i] for i in range(10)),
        negative="منفی",
        ordinal_suffix="م",
    )
