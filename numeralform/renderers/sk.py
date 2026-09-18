"""Slovak canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import IntegerFractionDecimalRenderer, locale_data


class SlovakRenderer(IntegerFractionDecimalRenderer):
    locale = "sk"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "sk",
        tuple(CARDINALS["sk"][i] for i in range(10)),
        omit_one_scales=frozenset({1_000, 1_000_000}),
        negative="mínus",
    )

    def _scale_prefix(self, scale: int, quotient: int) -> str:
        if scale == 1_000 and quotient == 2:
            return "dve"
        return super()._scale_prefix(scale, quotient)

    def _scale_name(self, scale: int, quotient: int) -> str:
        if scale == 1_000:
            return "tisíc"
        if scale == 1_000_000:
            if quotient == 1:
                return "milión"
            if quotient in (2, 3, 4):
                return "milióny"
            return "miliónov"
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
        if scale == 1_000:
            return f"{prefix}{scale_name}{suffix}"
        if scale == 1_000_000:
            separator = " " if remainder >= 1_000 else ""
            return f"{prefix} {scale_name}{separator}{suffix}"
        return super()._join_scale(
            scale=scale,
            quotient=quotient,
            prefix=prefix,
            scale_name=scale_name,
            remainder=remainder,
            suffix=suffix,
        )
