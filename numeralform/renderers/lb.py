"""Luxembourgish standalone numerals."""

from typing import ClassVar

from ._foundation import FoundationRenderer
from ._shared import locale_data

_ONES = (
    "null",
    "eent",
    "zwee",
    "dräi",
    "véier",
    "fënnef",
    "sechs",
    "siwen",
    "aacht",
    "néng",
)
_CARDINALS = {i: word for i, word in enumerate(_ONES)}
_CARDINALS.update(
    {
        10: "zéng",
        11: "elef",
        12: "zwielef",
        13: "dräizéng",
        14: "véierzéng",
        15: "fofzéng",
        16: "siechzéng",
        17: "siwwenzéng",
        18: "uechtzéng",
        19: "nonzéng",
    }
)
_CARDINALS.update(
    {
        20: "zwanzeg",
        30: "drësseg",
        40: "véierzeg",
        50: "fofzeg",
        60: "siechzeg",
        70: "siwwenzeg",
        80: "achtzeg",
        90: "nonzeg",
    }
)
_CARDINALS.update(
    {
        ten + i: f"{_ONES[i]}an{word}"
        for ten, word in (
            (20, "zwanzeg"),
            (30, "drësseg"),
            (40, "véierzeg"),
            (50, "fofzeg"),
            (60, "siechzeg"),
            (70, "siwwenzeg"),
            (80, "achtzeg"),
            (90, "nonzeg"),
        )
        for i in range(1, 10)
    }
)


class LuxembourgishRenderer(FoundationRenderer):
    locale = "lb"
    cardinals = _CARDINALS
    exact: ClassVar[dict[int, str]] = {100: "honnert", 1_000: "dausend"}
    data = locale_data("lb", _ONES, negative="minus", omit_one_scales=frozenset())
