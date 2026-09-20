"""Albanian standalone numerals."""

from typing import ClassVar

from ._foundation import FoundationRenderer
from ._shared import locale_data

_ONES = (
    "zero",
    "një",
    "dy",
    "tre",
    "katër",
    "pesë",
    "gjashtë",
    "shtatë",
    "tetë",
    "nëntë",
)
_CARDINALS = {i: word for i, word in enumerate(_ONES)}
_CARDINALS.update(
    {
        10: "dhjetë",
        11: "njëmbëdhjetë",
        12: "dymbëdhjetë",
        13: "trembëdhjetë",
        14: "katërmbëdhjetë",
        15: "pesëmbëdhjetë",
        16: "gjashtëmbëdhjetë",
        17: "shtatëmbëdhjetë",
        18: "tetëmbëdhjetë",
        19: "nëntëmbëdhjetë",
        20: "njëzet",
        30: "tridhjetë",
        40: "dyzet",
        50: "pesëdhjetë",
        60: "gjashtëdhjetë",
        70: "shtatëdhjetë",
        80: "tetëdhjetë",
        90: "nëntëdhjetë",
    }
)
_CARDINALS.update(
    {
        ten + i: f"{word} e {_ONES[i]}"
        for ten, word in (
            (20, "njëzet"),
            (30, "tridhjetë"),
            (40, "dyzet"),
            (50, "pesëdhjetë"),
            (60, "gjashtëdhjetë"),
            (70, "shtatëdhjetë"),
            (80, "tetëdhjetë"),
            (90, "nëntëdhjetë"),
        )
        for i in range(1, 10)
    }
)


class AlbanianRenderer(FoundationRenderer):
    locale = "sq"
    cardinals = _CARDINALS
    exact: ClassVar[dict[int, str]] = {100: "njëqind", 1_000: "një mijë"}
    data = locale_data("sq", _ONES, negative="minus", omit_one_scales=frozenset())
