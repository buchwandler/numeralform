"""Georgian standalone numerals."""

from typing import ClassVar

from ._foundation import FoundationRenderer
from ._shared import locale_data

_ONES = ("ნული", "ერთი", "ორი", "სამი", "ოთხი", "ხუთი", "ექვსი", "შვიდი", "რვა", "ცხრა")
_CARDINALS = {i: word for i, word in enumerate(_ONES)}
_CARDINALS.update(
    {
        10: "ათი",
        11: "თერთმეტი",
        12: "თორმეტი",
        13: "ცამეტი",
        14: "თოთხმეტი",
        15: "თხუთმეტი",
        16: "თექვსმეტი",
        17: "ჩვიდმეტი",
        18: "თვრამეტი",
        19: "ცხრამეტი",
    }
)
_CARDINALS.update(
    {
        20: "ოცი",
        30: "ოცდაათი",
        40: "ორმოცი",
        50: "ორმოცდაათი",
        60: "სამოცი",
        70: "სამოცდაათი",
        80: "ოთხმოცი",
        90: "ოთხმოცდაათი",
    }
)
_CARDINALS.update(
    {
        ten + i: f"{word[:-2] if word.endswith('ათი') else word}და{_ONES[i]}"
        for ten, word in (
            (20, "ოცი"),
            (30, "ოცდაათი"),
            (40, "ორმოცი"),
            (50, "ორმოცდაათი"),
            (60, "სამოცი"),
            (70, "სამოცდაათი"),
            (80, "ოთხმოცი"),
            (90, "ოთხმოცდაათი"),
        )
        for i in range(1, 10)
    }
)


class GeorgianRenderer(FoundationRenderer):
    locale = "ka"
    cardinals = _CARDINALS
    exact: ClassVar[dict[int, str]] = {100: "ასი", 1_000: "ათასი"}
    data = locale_data("ka", _ONES, negative="მინუს", omit_one_scales=frozenset())
