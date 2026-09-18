"""Telugu canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class TeluguRenderer(LexicalRenderer):
    locale = "te"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "te",
        tuple(CARDINALS["te"][i] for i in range(10)),
        negative="మైనస్",
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
        # A scale noun directly followed by a sub-hundred remainder takes
        # the plural ల suffix (వందల, వేయిల, లక్షల).
        if 0 < remainder < 100:
            scale_name += "ల"
        return super()._join_scale(
            scale=scale,
            quotient=quotient,
            prefix=prefix,
            scale_name=scale_name,
            remainder=remainder,
            suffix=suffix,
        )
