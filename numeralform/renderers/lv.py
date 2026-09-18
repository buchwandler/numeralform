"""Latvian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import IntegerFractionDecimalRenderer, locale_data


class LatvianRenderer(IntegerFractionDecimalRenderer):
    locale = "lv"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "lv",
        tuple(CARDINALS["lv"][i] for i in range(10)),
        omit_one_scales=frozenset({1_000, 1_000_000}),
        singular_after_x1=True,
        negative="mīnus",
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
        # Exactly one hundred plus units takes the genitive "simtu".
        if scale == 100 and quotient == 1 and 0 < remainder < 10:
            scale_name = "simtu"
        return super()._join_scale(
            scale=scale,
            quotient=quotient,
            prefix=prefix,
            scale_name=scale_name,
            remainder=remainder,
            suffix=suffix,
        )
