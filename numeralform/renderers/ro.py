"""Romanian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data

_FEMININE_HUNDRED = {"unu": "o", "doi": "două", "doisprezece": "douăsprezece"}


class RomanianRenderer(LexicalRenderer):
    locale = "ro"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "ro",
        tuple(CARDINALS["ro"][i] for i in range(10)),
        omit_one_scales=frozenset(),
    )

    def _scale_prefix(self, scale: int, quotient: int) -> str:
        if scale == 1_000:
            if quotient == 1:
                return "o"
            if quotient == 2:
                return "două"
        if scale == 1_000_000:
            if quotient == 1:
                return "un"
            if quotient == 2:
                return "două"
        prefix = super()._scale_prefix(scale, quotient)
        if scale in (1_000, 1_000_000):
            if 10 < quotient < 20:
                words = prefix.split(" ")
                words[-1] = "douăsprezece" if words[-1] == "doisprezece" else words[-1]
                return " ".join(words)
            if 20 < quotient < 100 and quotient % 10 == 2:
                words = prefix.split(" ")
                words[-1] = "două" if words[-1] == "doi" else words[-1]
                return " ".join(words)
            return prefix
        if scale == 100:
            words = prefix.split(" ")
            if words:
                words[-1] = _FEMININE_HUNDRED.get(words[-1], words[-1])
            return " ".join(words)
        return prefix

    def _scale_name(self, scale: int, quotient: int) -> str:
        if scale == 1_000:
            if quotient == 1:
                return "mie"
            if quotient < 20:
                return "mii"
            return "de mii"
        if scale == 1_000_000:
            return "milion" if quotient == 1 else "milioane"
        return super()._scale_name(scale, quotient)
