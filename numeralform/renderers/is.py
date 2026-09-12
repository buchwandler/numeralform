# ruff: noqa: N999
"""Icelandic canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class IcelandicRenderer(LexicalRenderer):
    locale = "is"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data("is", tuple(CARDINALS["is"][i] for i in range(10)))
