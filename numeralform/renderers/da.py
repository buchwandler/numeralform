"""Danish canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class DanishRenderer(LexicalRenderer):
    locale = "da"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data("da", tuple(CARDINALS["da"][i] for i in range(10)), compound="")

    def _scale_name(self, scale: int, quotient: int) -> str:
        if scale == 1_000_000:
            # Danish uses the plural form for every quotient, including one.
            return "millioner"
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
            if quotient == 1:
                # One thousand is written as the single word "ettusind".
                result = "ettusind"
                if remainder:
                    result = f"ettusinde og {suffix}"
                return result
            if quotient <= 100:
                # Below one hundred, and exactly one hundred, the "e" form
                # coordinates the remainder with "og".
                result = f"{prefix}{scale_name}"
                if remainder:
                    result = f"{result}e og {suffix}"
                return result
            # From two hundred up the remainder compounds directly.
            result = f"{prefix}{scale_name}"
            if remainder:
                result = f"{result}{suffix}"
            return result
        if scale == 1_000_000 and quotient == 1:
            prefix = "en"
        result = f"{prefix} {scale_name}"
        if remainder:
            result = f"{result} {suffix}"
        return result
