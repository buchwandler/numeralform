"""Kurmanji/Northern Kurdish numerals in Hawar Latin orthography.

The ``ku`` foundation policy is the Kurmanji surface requested by ``ku_TR``;
Sorani is intentionally not claimed by this renderer.
"""

from typing import ClassVar

from ._foundation import FoundationRenderer
from ._shared import locale_data

_ONES = ("sifir", "yek", "du", "sê", "çar", "pênc", "şeş", "heft", "heşt", "neh")
_CARDINALS = {i: word for i, word in enumerate(_ONES)}
_CARDINALS.update(
    {
        10: "deh",
        11: "yanzde",
        12: "dwanzde",
        13: "sêzde",
        14: "çardeh",
        15: "panzdeh",
        16: "şanzdeh",
        17: "hevdeh",
        18: "hejdeh",
        19: "nozdeh",
    }
)
_CARDINALS.update(
    {
        20: "bîst",
        30: "sî",
        40: "çil",
        50: "pêncî",
        60: "şêst",
        70: "heftê",
        80: "heştê",
        90: "nod",
    }
)
_CARDINALS.update(
    {
        ten + i: f"{word} û {_ONES[i]}"
        for ten, word in (
            (20, "bîst"),
            (30, "sî"),
            (40, "çil"),
            (50, "pêncî"),
            (60, "şêst"),
            (70, "heftê"),
            (80, "heştê"),
            (90, "nod"),
        )
        for i in range(1, 10)
    }
)


class KurdishRenderer(FoundationRenderer):
    locale = "ku"
    cardinals = _CARDINALS
    exact: ClassVar[dict[int, str]] = {100: "sed", 1_000: "hezar"}
    data = locale_data("ku", _ONES, negative="neyînî", omit_one_scales=frozenset())
