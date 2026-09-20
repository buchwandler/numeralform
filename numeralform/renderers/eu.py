"""Basque numerals using the reviewed vigesimal count system."""

from typing import ClassVar

from ._foundation import FoundationRenderer
from ._shared import locale_data

_ONES = (
    "zero",
    "bat",
    "bi",
    "hiru",
    "lau",
    "bost",
    "sei",
    "zazpi",
    "zortzi",
    "bederatzi",
)
_CARDINALS = {i: word for i, word in enumerate(_ONES)}
_CARDINALS.update(
    {
        10: "hamar",
        11: "hamaika",
        12: "hamabi",
        13: "hamahiru",
        14: "hamalau",
        15: "hamabost",
        16: "hamasei",
        17: "hamazazpi",
        18: "hemezortzi",
        19: "hemeretzi",
    }
)
_CARDINALS.update({20: "hogei", 40: "berrogei", 60: "hirurogei", 80: "laurogei"})
for _base, _word in (
    (20, "hogei"),
    (40, "berrogei"),
    (60, "hirurogei"),
    (80, "laurogei"),
):
    for _i in range(1, 20):
        if _base + _i < 100:
            _CARDINALS[_base + _i] = (
                f"{_word}ta {_ONES[_i]}" if _i < 10 else f"{_word}ta {_CARDINALS[_i]}"
            )


class BasqueRenderer(FoundationRenderer):
    locale = "eu"
    cardinals = _CARDINALS
    exact: ClassVar[dict[int, str]] = {100: "ehun", 1_000: "mila"}
    data = locale_data("eu", _ONES, negative="minus", omit_one_scales=frozenset())
