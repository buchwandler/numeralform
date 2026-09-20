"""Estonian standalone numerals."""

from typing import ClassVar

from ._foundation import FoundationRenderer
from ._shared import locale_data

_ONES = (
    "null",
    "üks",
    "kaks",
    "kolm",
    "neli",
    "viis",
    "kuus",
    "seitse",
    "kaheksa",
    "üheksa",
)
_TEENS = (
    "kümme",
    "üksteist",
    "kaksteist",
    "kolmteist",
    "neliteist",
    "viisteist",
    "kuusteist",
    "seitseteist",
    "kaheksateist",
    "üheksateist",
)
_TENS = {
    20: "kakskümmend",
    30: "kolmkümmend",
    40: "nelikümmend",
    50: "viiskümmend",
    60: "kuuskümmend",
    70: "seitsekümmend",
    80: "kaheksakümmend",
    90: "üheksakümmend",
}
_CARDINALS = {i: word for i, word in enumerate(_ONES)}
_CARDINALS.update({10 + i: word for i, word in enumerate(_TEENS)})
_CARDINALS.update({ten: word for ten, word in _TENS.items()})
_CARDINALS.update(
    {ten + i: f"{word} {_ONES[i]}" for ten, word in _TENS.items() for i in range(1, 10)}
)


class EstonianRenderer(FoundationRenderer):
    locale = "et"
    cardinals = _CARDINALS
    exact: ClassVar[dict[int, str]] = {100: "sada", 1_000: "tuhat"}
    data = locale_data("et", _ONES, negative="miinus", omit_one_scales=frozenset())
