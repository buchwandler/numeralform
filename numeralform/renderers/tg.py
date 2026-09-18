"""Tajik canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class TajikRenderer(LexicalRenderer):
    locale = "tg"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "tg",
        tuple(CARDINALS["tg"][i] for i in range(10)),
        negative="минус",
        omit_one_scales=frozenset(),
    )

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
        # The scale noun takes the coordinating suffix у before a remainder.
        if remainder:
            scale_name += "у"
            if remainder == 100:
                # A bare hundred remainder reads яксад after a scale noun.
                suffix = "яксад"
        return super()._join_scale(
            scale=scale,
            quotient=quotient,
            prefix=prefix,
            scale_name=scale_name,
            remainder=remainder,
            suffix=suffix,
        )
