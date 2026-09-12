"""Turkish canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class TurkishRenderer(LexicalRenderer):
    locale = "tr"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "tr",
        tuple(CARDINALS["tr"][i] for i in range(10)),
        compound="",
        negative="eksi",
        ordinal_suffix="inci",
    )
