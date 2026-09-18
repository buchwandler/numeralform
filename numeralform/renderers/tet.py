"""Tetum canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data


class TetumRenderer(LexicalRenderer):
    locale = "tet"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "tet",
        tuple(CARDINALS["tet"][i] for i in range(10)),
        compound=" ",
        negative="menus",
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
        # Tetum places the scale noun before its multiplier.
        result = f"{scale_name} {prefix}".strip()
        if remainder:
            connector = " "
            if remainder < 10:
                value = quotient * scale + remainder
                digits = str(value)
                # A unit added to an otherwise round number joins directly;
                # otherwise the coordinating "resin" is used.
                if not all(digit == "0" for digit in digits[1:-1]):
                    connector = " resin "
            result = f"{result}{connector}{suffix}"
        return result
