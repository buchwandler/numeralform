"""Dutch canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class DutchRenderer(LexicalRenderer):
    locale = "nl"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "nl",
        tuple(CARDINALS["nl"][i] for i in range(10)),
        compound="",
        negative="min",
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
        if scale == 1_000_000:
            # Dutch compounds below a million but writes "miljoen" separately.
            result = f"{prefix} {scale_name}"
            if remainder:
                result = f"{result} {suffix}"
            return result
        return super()._join_scale(
            scale=scale,
            quotient=quotient,
            prefix=prefix,
            scale_name=scale_name,
            remainder=remainder,
            suffix=suffix,
        )
