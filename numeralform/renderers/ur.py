"""Urdu standalone numerals."""

from typing import ClassVar

from ._foundation import FoundationRenderer
from ._shared import locale_data

_ONES = ("صفر", "ایک", "دو", "تین", "چار", "پانچ", "چھ", "سات", "آٹھ", "نو")
_CARDINALS = {i: word for i, word in enumerate(_ONES)}
_CARDINALS.update(
    {
        10: "دس",
        11: "گیارہ",
        12: "بارہ",
        13: "تیرہ",
        14: "چودہ",
        15: "پندرہ",
        16: "سولہ",
        17: "سترہ",
        18: "اٹھارہ",
        19: "انیس",
        20: "بیس",
        21: "اکیس",
        22: "بائیس",
        23: "تئیس",
        24: "چوبیس",
        25: "پچیس",
        26: "چھبیس",
        27: "ستائیس",
        28: "اٹھائیس",
        29: "انتیس",
        30: "تیس",
        31: "اکتیس",
        32: "بتیس",
        33: "تینتیس",
        34: "چونتیس",
        35: "پینتیس",
        36: "چھتیس",
        37: "سینتیس",
        38: "اڑتیس",
        39: "انتالیس",
        40: "چالیس",
        50: "پچاس",
        60: "ساٹھ",
        70: "ستر",
        80: "اسی",
        90: "نوے",
    }
)


class UrduRenderer(FoundationRenderer):
    locale = "ur"
    cardinals = _CARDINALS
    exact: ClassVar[dict[int, str]] = {100: "ایک سو", 1_000: "ایک ہزار"}
    data = locale_data("ur", _ONES, negative="منفی", omit_one_scales=frozenset())
