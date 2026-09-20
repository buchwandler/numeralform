"""Malayalam standalone/count numerals."""

from typing import ClassVar

from ._foundation import FoundationRenderer
from ._shared import locale_data

_ONES = ("പൂജ്യം", "ഒന്ന്", "രണ്ട്", "മൂന്ന്", "നാല്", "അഞ്ച്", "ആറ്", "ഏഴ്", "എട്ട്", "ഒൻപത്")
_TEENS = {
    10: "പത്ത്",
    11: "പതിനൊന്ന്",
    12: "പന്ത്രണ്ട്",
    13: "പതിമൂന്ന്",
    14: "പതിനാല്",
    15: "പതിനഞ്ച്",
    16: "പതിനാറ്",
    17: "പതിനേഴ്",
    18: "പതിനെട്ട്",
    19: "പത്തൊൻപത്",
}
_TENS = {
    20: "ഇരുപത്",
    30: "മുപ്പത്",
    40: "നാൽപ്പത്",
    50: "അൻപത്",
    60: "അറുപത്",
    70: "എഴുപത്",
    80: "എൺപത്",
    90: "തൊണ്ണൂറ്",
}
_CARDINALS = {i: word for i, word in enumerate(_ONES)}
_CARDINALS.update(_TEENS)
_CARDINALS.update(_TENS)
_CARDINALS.update(
    {ten + i: f"{word} {_ONES[i]}" for ten, word in _TENS.items() for i in range(1, 10)}
)


class MalayalamRenderer(FoundationRenderer):
    locale = "ml"
    cardinals = _CARDINALS
    exact: ClassVar[dict[int, str]] = {100: "നൂറ്", 1_000: "ആയിരം"}
    data = locale_data("ml", _ONES, negative="മൈനസ്", omit_one_scales=frozenset())
