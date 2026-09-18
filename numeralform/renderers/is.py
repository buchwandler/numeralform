# ruff: noqa: N999
"""Icelandic canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data

_NEUTER_PREFIX = {"einn": "eitt", "tveir": "tvö", "þrír": "þrjú", "fjórir": "fjögur"}
_FEMININE_PREFIX = {"einn": "ein", "tveir": "tvær", "þrír": "þrjár", "fjórir": "fjórar"}


class IcelandicRenderer(LexicalRenderer):
    locale = "is"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "is",
        tuple(CARDINALS["is"][i] for i in range(10)),
        negative="mínus",
        omit_one_scales=frozenset(),
    )

    def _scale_prefix(self, scale: int, quotient: int) -> str:
        prefix = super()._scale_prefix(scale, quotient)
        words = prefix.split(" ")
        if not words:
            return prefix
        if scale == 1_000_000:
            words[-1] = _FEMININE_PREFIX.get(words[-1], words[-1])
        else:
            words[-1] = _NEUTER_PREFIX.get(words[-1], words[-1])
        return " ".join(words)

    def _scale_name(self, scale: int, quotient: int) -> str:
        if scale == 1_000_000:
            return (
                "milljón"
                if quotient % 10 == 1 and quotient % 100 != 11
                else "milljónir"
            )
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
            # The coordinating "og" appears before an atomic remainder
            # (a sub-hundred phrase or exactly one hundred) that does not
            # itself coordinate tens and units.
            connector = "" if (remainder > 100 or " og " in suffix) else "og "
            result = f"{result}{self.data.compound}{connector}{suffix}".strip()
        return result
