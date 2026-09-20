"""Greek standalone/count numerals."""

from typing import ClassVar

from ._foundation import FoundationRenderer
from ._shared import locale_data

_ONES = (
    "μηδέν",
    "ένα",
    "δύο",
    "τρία",
    "τέσσερα",
    "πέντε",
    "έξι",
    "επτά",
    "οκτώ",
    "εννέα",
)
_TEENS = (
    "δέκα",
    "έντεκα",
    "δώδεκα",
    "δεκατρία",
    "δεκατέσσερα",
    "δεκαπέντε",
    "δεκαέξι",
    "δεκαεπτά",
    "δεκαοκτώ",
    "δεκαεννέα",
)
_TENS = {
    20: "είκοσι",
    30: "τριάντα",
    40: "σαράντα",
    50: "πενήντα",
    60: "εξήντα",
    70: "εβδομήντα",
    80: "ογδόντα",
    90: "ενενήντα",
}
_CARDINALS = {i: word for i, word in enumerate(_ONES)}
_CARDINALS.update({10 + i: word for i, word in enumerate(_TEENS)})
_CARDINALS.update({ten: word for ten, word in _TENS.items()})
_CARDINALS.update(
    {ten + i: f"{word} {_ONES[i]}" for ten, word in _TENS.items() for i in range(1, 10)}
)


class GreekRenderer(FoundationRenderer):
    locale = "el"
    cardinals = _CARDINALS
    exact: ClassVar[dict[int, str]] = {100: "εκατό", 1_000: "χίλια"}
    data = locale_data("el", _ONES, negative="μείον", omit_one_scales=frozenset())
