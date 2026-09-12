"""Tetum canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class TetumRenderer(LexicalRenderer):
    locale = "tet"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "tet", tuple(CARDINALS["tet"][i] for i in range(10)), negative="menus"
    )
