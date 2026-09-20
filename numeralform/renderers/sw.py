"""Swahili standalone numerals."""

from typing import ClassVar

from ._foundation import FoundationRenderer
from ._shared import locale_data

_ONES = (
    "sifuri",
    "moja",
    "mbili",
    "tatu",
    "nne",
    "tano",
    "sita",
    "saba",
    "nane",
    "tisa",
)
_CARDINALS = {i: word for i, word in enumerate(_ONES)}
_CARDINALS.update(
    {
        10: "kumi",
        11: "kumi na moja",
        12: "kumi na mbili",
        13: "kumi na tatu",
        14: "kumi na nne",
        15: "kumi na tano",
        16: "kumi na sita",
        17: "kumi na saba",
        18: "kumi na nane",
        19: "kumi na tisa",
        20: "ishirini",
        30: "thelathini",
        40: "arobaini",
        50: "hamsini",
        60: "sitini",
        70: "sabini",
        80: "themanini",
        90: "tisini",
    }
)
_CARDINALS.update(
    {
        ten + i: f"{word} na {_ONES[i]}"
        for ten, word in (
            (20, "ishirini"),
            (30, "thelathini"),
            (40, "arobaini"),
            (50, "hamsini"),
            (60, "sitini"),
            (70, "sabini"),
            (80, "themanini"),
            (90, "tisini"),
        )
        for i in range(1, 10)
    }
)


class SwahiliRenderer(FoundationRenderer):
    locale = "sw"
    cardinals = _CARDINALS
    exact: ClassVar[dict[int, str]] = {100: "mia moja", 1_000: "elfu moja"}
    data = locale_data("sw", _ONES, negative="hasi", omit_one_scales=frozenset())
