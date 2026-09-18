"""Arabic canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data

_AND = "و "


def _arabic_scale_word(scale: int, quotient: int, remainder: int) -> str:
    thousand = scale == 1_000
    if quotient == 1:
        return "ألف" if thousand else "مليون"
    if quotient == 2:
        return "ألفان" if thousand else "مليونان"
    if quotient <= 10:
        return "آلاف" if thousand else "ملايين"
    if remainder:
        return "ألفاً" if thousand else "مليوناً"
    return "ألف" if thousand else "مليون"


class ArabicRenderer(LexicalRenderer):
    locale = "ar"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "ar",
        tuple(CARDINALS["ar"][i] for i in range(10)),
        negative="سالب",
        omit_one_scales=frozenset({1_000, 1_000_000}),
    )

    def _scale_prefix(self, scale: int, quotient: int) -> str:
        if quotient == 2 and scale in (1_000, 1_000_000):
            return ""
        return super()._scale_prefix(scale, quotient)

    def _scale_name(self, scale: int, quotient: int) -> str:
        if scale in (1_000, 1_000_000):
            return _arabic_scale_word(scale, quotient, 0)
        return super()._scale_name(scale, quotient)

    def _join_scale(
        self,
        *,
        scale: int,
        quotient: int,
        prefix: str,
        scale_name: str,
        remainder: int,
        suffix: str,
    ) -> str:
        if scale in (1_000, 1_000_000):
            scale_name = _arabic_scale_word(scale, quotient, remainder)
            # Exactly two hundred takes the construct form before a bare
            # scale noun; the accusative مليوناً keeps the nominative.
            if prefix == "مئتان" and not (
                scale == 1_000_000 and scale_name == "مليوناً"
            ):
                prefix = "مئتا"
        result = f"{prefix}{self.data.compound}{scale_name}".strip()
        if remainder:
            result = f"{result}{self.data.compound}{_AND}{suffix}".strip()
        return result
