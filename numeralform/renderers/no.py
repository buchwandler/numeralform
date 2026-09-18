"""Norwegian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class NorwegianRenderer(LexicalRenderer):
    locale = "no"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "no",
        tuple(CARDINALS["no"][i] for i in range(10)),
        compound=" ",
        omit_one_scales=frozenset(),
    )

    def _scale_name(self, scale: int, quotient: int) -> str:
        if scale == 1_000_000:
            # Norwegian does not pluralize "million" in numerals.
            return "million"
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
        result = f"{prefix}{self.data.compound}{scale_name}".strip()
        if remainder:
            # The coordinating "og" appears before a sub-hundred remainder.
            connector = "og " if remainder < 100 else ""
            result = f"{result}{self.data.compound}{connector}{suffix}".strip()
        return result
