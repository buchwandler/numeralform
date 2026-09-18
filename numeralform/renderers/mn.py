"""Mongolian canonical numeral renderer."""

from ..errors import InvalidValueError
from ..model import DecimalNumber
from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data

_COMPLETE_CARDINALS = {
    0: "тэг",
    1: "нэг",
    2: "хоёр",
    3: "гурав",
    4: "дөрөв",
    5: "тав",
    6: "зургаа",
    7: "долоо",
    8: "найм",
    9: "ес",
    10: "арав",
    11: "арван нэг",
    12: "арван хоёр",
    13: "арван гурав",
    14: "арван дөрөв",
    15: "арван тав",
    16: "арван зургаа",
    17: "арван долоо",
    18: "арван найм",
    19: "арван ес",
    20: "хорь",
    21: "хорин нэг",
    22: "хорин хоёр",
    23: "хорин гурав",
    24: "хорин дөрөв",
    25: "хорин тав",
    26: "хорин зургаа",
    27: "хорин долоо",
    28: "хорин найм",
    29: "хорин ес",
    30: "гуч",
    31: "гучин нэг",
    32: "гучин хоёр",
    33: "гучин гурав",
    34: "гучин дөрөв",
    35: "гучин тав",
    36: "гучин зургаа",
    37: "гучин долоо",
    38: "гучин найм",
    39: "гучин ес",
    40: "дөч",
    41: "дөчин нэг",
    42: "дөчин хоёр",
    43: "дөчин гурав",
    44: "дөчин дөрөв",
    45: "дөчин тав",
    46: "дөчин зургаа",
    47: "дөчин долоо",
    48: "дөчин найм",
    49: "дөчин ес",
    50: "тавь",
    51: "тавин нэг",
    52: "тавин хоёр",
    53: "тавин гурав",
    54: "тавин дөрөв",
    55: "тавин тав",
    56: "тавин зургаа",
    57: "тавин долоо",
    58: "тавин найм",
    59: "тавин ес",
    60: "жар",
    61: "жаран нэг",
    62: "жаран хоёр",
    63: "жаран гурав",
    64: "жаран дөрөв",
    65: "жаран тав",
    66: "жаран зургаа",
    67: "жаран долоо",
    68: "жаран найм",
    69: "жаран ес",
    70: "дал",
    71: "далан нэг",
    72: "далан хоёр",
    73: "далан гурав",
    74: "далан дөрөв",
    75: "далан тав",
    76: "далан зургаа",
    77: "далан долоо",
    78: "далан найм",
    79: "далан ес",
    80: "ная",
    81: "наян нэг",
    82: "наян хоёр",
    83: "наян гурав",
    84: "наян дөрөв",
    85: "наян тав",
    86: "наян зургаа",
    87: "наян долоо",
    88: "наян найм",
    89: "наян ес",
    90: "ер",
    91: "ерэн нэг",
    92: "ерэн хоёр",
    93: "ерэн гурав",
    94: "ерэн дөрөв",
    95: "ерэн тав",
    96: "ерэн зургаа",
    97: "ерэн долоо",
    98: "ерэн найм",
    99: "ерэн ес",
}

# Stale pre-review exact entries at and above 100 are dropped; the
# reviewed composition rules own every scale form.
_FIXTURE_CARDINALS = {k: v for k, v in CARDINALS["mn"].items() if k < 100}
_CARDINALS = {**_FIXTURE_CARDINALS, **_COMPLETE_CARDINALS}

# Attributive/genitive numeral stems used before scale nouns (зуу, мянга, сая).
_ATTRIBUTIVE = {
    "нэг": "нэг",
    "хоёр": "хоёр",
    "гурав": "гурван",
    "дөрөв": "дөрвөн",
    "тав": "таван",
    "зургаа": "зургаан",
    "долоо": "долоон",
    "найм": "найман",
    "ес": "есөн",
    "арав": "арван",
    "хорь": "хорин",
    "гуч": "гучин",
    "дөч": "дөчин",
    "тавь": "тавин",
    "жар": "жаран",
    "дал": "далан",
    "ная": "наян",
    "ер": "ерэн",
    "зуу": "зуун",
    "мянга": "мянган",
    "сая": "саян",
}


class MongolianRenderer(LexicalRenderer):
    locale = "mn"
    cardinals = _CARDINALS
    ordinals = ORDINALS[locale]
    data = locale_data(
        "mn",
        tuple(_CARDINALS[i] for i in range(10)),
        negative="хасах",
        omit_one_scales=frozenset({100}),
    )

    def _scale_prefix(self, scale: int, quotient: int) -> str:
        prefix = super()._scale_prefix(scale, quotient)
        words = prefix.split(" ")
        if words:
            words[-1] = _ATTRIBUTIVE.get(words[-1], words[-1])
        return " ".join(words)

    def _join_scale(
        self,
        *,
        scale: int,
        quotient: int,
        prefix: str,
        scale_name: str,
        remainder: int,
        suffix: str,
    ) -> str:
        if scale == 100 and remainder:
            scale_name = "зуун"
        return super()._join_scale(
            scale=scale,
            quotient=quotient,
            prefix=prefix,
            scale_name=scale_name,
            remainder=remainder,
            suffix=suffix,
        )

    def _year(self, value: int) -> str:
        if value < 0 or value > 9999:
            raise InvalidValueError(
                f"{self.locale} year value is outside the supported range"
            )
        words = self._cardinal(value).split(" ")
        words[-1] = _ATTRIBUTIVE.get(words[-1], words[-1])
        return f"{' '.join(words)} он"

    def _decimal(self, value: object) -> str:
        if not isinstance(value, DecimalNumber):
            raise InvalidValueError("decimal form requires DecimalNumber or Decimal")
        integer = self._cardinal(int(value.integer))
        if value.negative:
            integer = f"хасах {integer}"
        fraction = int(value.fraction)
        denominator = _DECIMAL_DENOMINATORS[len(value.fraction)]
        fraction_words = self._cardinal(fraction) if fraction else "тэг"
        return f"{integer}, {denominator} {fraction_words}"


_DECIMAL_DENOMINATORS = {
    1: "аравны",
    2: "зууны",
    3: "мянганы",
    4: "арван мянганы",
}
