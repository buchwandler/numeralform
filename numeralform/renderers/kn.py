"""Kannada canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data

# Scale nouns that take the genitive connective before a sub-hundred
# remainder (ಸಾವಿರದ, ಲಕ್ಷದ).
_CONNECTIVE_SCALES = frozenset({1_000, 100_000})


class KannadaRenderer(LexicalRenderer):
    locale = "kn"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "kn",
        tuple(CARDINALS["kn"][i] for i in range(10)),
        negative="ಮೈನಸ್",
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
        if scale in _CONNECTIVE_SCALES and 0 < remainder < 100:
            scale_name += "ದ"
        return super()._join_scale(
            scale=scale,
            quotient=quotient,
            prefix=prefix,
            scale_name=scale_name,
            remainder=remainder,
            suffix=suffix,
        )
