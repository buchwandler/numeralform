"""Persian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data

_AND = "و "


class PersianRenderer(LexicalRenderer):
    locale = "fa"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "fa",
        tuple(CARDINALS["fa"][i] for i in range(10)),
        negative="منفی",
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
        result = f"{prefix}{self.data.compound}{scale_name}".strip()
        if remainder:
            result = f"{result}{self.data.compound}{_AND}{suffix}".strip()
        return result
