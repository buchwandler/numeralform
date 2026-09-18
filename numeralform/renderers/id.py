"""Indonesian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data

_CONTRACTED_PREFIX_SCALES = {100: "seratus", 1_000: "seribu"}


class IndonesianRenderer(LexicalRenderer):
    locale = "id"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "id", tuple(CARDINALS["id"][i] for i in range(10)), negative="min"
    )

    def _scale_prefix(self, scale: int, quotient: int) -> str:
        if quotient == 1 and scale in _CONTRACTED_PREFIX_SCALES:
            return ""
        return self._compose(quotient)

    def _scale_name(self, scale: int, quotient: int) -> str:
        if quotient == 1 and scale in _CONTRACTED_PREFIX_SCALES:
            return _CONTRACTED_PREFIX_SCALES[scale]
        return super()._scale_name(scale, quotient)

    def _compose(self, value: int) -> str:
        if value < 1_000_000:
            return super()._compose(value)
        millions, remainder = divmod(value, 1_000_000)
        parts = [f"{super()._compose(millions)} juta"]
        if remainder:
            thousands, rest = divmod(remainder, 1_000)
            if thousands:
                parts.append(
                    "satu ribu"
                    if thousands == 1
                    else f"{super()._compose(thousands)} ribu",
                )
            if rest:
                parts.append(super()._compose(rest))
        return " ".join(parts)
