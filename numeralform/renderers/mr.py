"""Marathi standalone numerals."""

from typing import ClassVar

from ._foundation import FoundationRenderer
from ._shared import locale_data

_ONES = ("शून्य", "एक", "दोन", "तीन", "चार", "पाच", "सहा", "सात", "आठ", "नऊ")
_CARDINALS = {i: word for i, word in enumerate(_ONES)}
_CARDINALS.update(
    {
        10: "दहा",
        11: "अकरा",
        12: "बारा",
        13: "तेरा",
        14: "चौदा",
        15: "पंधरा",
        16: "सोळा",
        17: "सतरा",
        18: "अठरा",
        19: "एकोणीस",
        20: "वीस",
        21: "एकवीस",
        22: "बावीस",
        23: "तेवीस",
        24: "चोवीस",
        25: "पंचवीस",
        26: "सव्वीस",
        27: "सत्तावीस",
        28: "अठ्ठावीस",
        29: "एकोणतीस",
        30: "तीस",
        31: "एकतीस",
        32: "बत्तीस",
        33: "तेहेतीस",
        34: "चौतीस",
        35: "पस्तीस",
        36: "छत्तीस",
        37: "सदतीस",
        38: "अडतीस",
        39: "एकोणचाळीस",
        40: "चाळीस",
        50: "पन्नास",
        60: "साठ",
        70: "सत्तर",
        80: "ऐंशी",
        90: "नव्वद",
    }
)


class MarathiRenderer(FoundationRenderer):
    locale = "mr"
    cardinals = _CARDINALS
    exact: ClassVar[dict[int, str]] = {100: "शंभर", 1_000: "हजार"}
    data = locale_data("mr", _ONES, negative="उणे", omit_one_scales=frozenset())
