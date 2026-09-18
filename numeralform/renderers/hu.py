"""Hungarian canonical numeral renderer."""

from ..errors import InvalidValueError
from ..model import DecimalNumber
from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data

_DENOMINATORS = {
    1: "tized",
    2: "század",
    3: "ezred",
    4: "tízezred",
}


class HungarianRenderer(LexicalRenderer):
    locale = "hu"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "hu",
        tuple(CARDINALS["hu"][i] for i in range(10)),
        compound="",
        negative="mínusz",
    )

    def _scale_prefix(self, scale: int, quotient: int) -> str:
        prefix = super()._scale_prefix(scale, quotient)
        if scale < 1_000:
            return prefix
        # Exactly two becomes "két" directly before ezer and millió.
        return "két" if prefix == "kettő" else prefix

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
        result = f"{prefix}{scale_name}"
        if remainder:
            # Numbers from 2000 up hyphenate between large groups;
            # 1000-1999 are written as single words.
            separator = "-" if scale == 1_000_000 or quotient >= 2 else ""
            if not separator and suffix == "kettő":
                # 1002 is written as the single word "ezerkét".
                suffix = "két"
            result = f"{result}{separator}{suffix}"
        return result

    def _decimal(self, value: object) -> str:
        if not isinstance(value, DecimalNumber):
            raise InvalidValueError("decimal form requires DecimalNumber or Decimal")
        integer = self._cardinal(int(value.integer))
        if value.negative:
            integer = f"mínusz {integer}"
        fraction = self._cardinal(int(value.fraction))
        denominator = _DENOMINATORS[len(value.fraction)]
        return f"{integer} egész {fraction} {denominator}"
