"""Bulgarian standalone/count numerals."""

from typing import ClassVar

from ._foundation import FoundationRenderer
from ._shared import locale_data

_ONES = (
    "нула",
    "едно",
    "две",
    "три",
    "четири",
    "пет",
    "шест",
    "седем",
    "осем",
    "девет",
)
_TEENS = (
    "десет",
    "единадесет",
    "дванадесет",
    "тринадесет",
    "четиринадесет",
    "петнадесет",
    "шестнадесет",
    "седемнадесет",
    "осемнадесет",
    "деветнадесет",
)
_TENS = {
    20: "двадесет",
    30: "тридесет",
    40: "четиридесет",
    50: "петдесет",
    60: "шестдесет",
    70: "седемдесет",
    80: "осемдесет",
    90: "деветдесет",
}
_CARDINALS = {i: word for i, word in enumerate(_ONES)}
_CARDINALS.update({10 + i: word for i, word in enumerate(_TEENS)})
_CARDINALS.update({ten: word for ten, word in _TENS.items()})
_CARDINALS.update(
    {
        ten + i: f"{word} и {_ONES[i]}"
        for ten, word in _TENS.items()
        for i in range(1, 10)
    }
)


class BulgarianRenderer(FoundationRenderer):
    locale = "bg"
    cardinals = _CARDINALS
    exact: ClassVar[dict[int, str]] = {100: "сто", 1_000: "хиляда"}
    data = locale_data("bg", _ONES, negative="минус", omit_one_scales=frozenset())
