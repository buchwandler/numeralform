"""Serbian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import IntegerFractionDecimalRenderer, locale_data

_FEMININE_THOUSAND = {"jedan": "jedna", "dva": "dve"}


class SerbianRenderer(IntegerFractionDecimalRenderer):
    locale = "sr"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "sr",
        tuple(CARDINALS["sr"][i] for i in range(10)),
        omit_one_scales=frozenset(),
        singular_after_x1=True,
    )

    def _scale_prefix(self, scale: int, quotient: int) -> str:
        prefix = super()._scale_prefix(scale, quotient)
        if scale != 1_000:
            return prefix
        words = prefix.split(" ")
        if words:
            words[-1] = _FEMININE_THOUSAND.get(words[-1], words[-1])
        return " ".join(words)
