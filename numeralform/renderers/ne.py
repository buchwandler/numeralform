"""Nepali standalone numerals using the CLDR 48.2 spelling policy."""

from typing import ClassVar

from ._foundation import FoundationRenderer
from ._shared import locale_data

_ONES = ("शून्य", "एक", "दुई", "तिन", "चार", "पाँच", "छ", "सात", "आठ", "नौ")
_CARDINALS = {i: word for i, word in enumerate(_ONES)}
_CARDINALS.update(
    {
        10: "दस",
        11: "एघार",
        12: "बाह्र",
        13: "तेह्र",
        14: "चौध",
        15: "पन्ध्र",
        16: "सोह्र",
        17: "सत्र",
        18: "अठार",
        19: "उन्नाइस",
        20: "बीस",
        21: "एक्काइस",
        22: "बाइस",
        23: "तेइस",
        24: "चौबीस",
        25: "पच्चीस",
        26: "छब्बीस",
        27: "सत्ताइस",
        28: "अट्ठाइस",
        29: "उनन्तीस",
        30: "तीस",
        40: "चालीस",
        50: "पचास",
        60: "साठी",
        70: "सत्तरी",
        80: "असी",
        90: "नब्बे",
    }
)


class NepaliRenderer(FoundationRenderer):
    locale = "ne"
    cardinals = _CARDINALS
    exact: ClassVar[dict[int, str]] = {100: "एक सय", 1_000: "एक हजार"}
    data = locale_data("ne", _ONES, negative="माइनस", omit_one_scales=frozenset())
