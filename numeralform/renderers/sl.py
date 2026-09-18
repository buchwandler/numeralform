"""Slovenian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data

_MASCULINE_PREFIX = {"ena": "en", "dve": "dva"}
_MASCULINE_MILLION_PREFIX = {"tri": "trije", "štiri": "štirje"}


class SlovenianRenderer(LexicalRenderer):
    locale = "sl"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "sl",
        tuple(CARDINALS["sl"][i] for i in range(10)),
        negative="minus",
        omit_one_scales=frozenset({100, 1_000, 1_000_000}),
    )

    def _scale_prefix(self, scale: int, quotient: int) -> str:
        prefix = super()._scale_prefix(scale, quotient)
        if scale < 1_000:
            return prefix
        words = prefix.split(" ")
        if not words:
            return prefix
        last = words[-1]
        if scale == 1_000_000:
            last = _MASCULINE_MILLION_PREFIX.get(last, last)
        last = _MASCULINE_PREFIX.get(last, last)
        words[-1] = last
        return " ".join(words)

    def _scale_name(self, scale: int, quotient: int) -> str:
        if scale == 1_000_000:
            remainder = quotient % 100
            if quotient == 1 or remainder == 1:
                return "milijon"
            if remainder == 2:
                return "milijona"
            if remainder in (3, 4):
                return "milijoni"
            return "milijonov"
        return super()._scale_name(scale, quotient)
