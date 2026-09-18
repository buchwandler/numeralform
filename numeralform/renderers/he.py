"""Hebrew canonical numeral renderer."""

from ..errors import InvalidValueError
from ..model import DecimalNumber
from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, decimal_policy, locale_data

_ONES_FEM = {
    1: "אחת",
    2: "שתיים",
    3: "שלוש",
    4: "ארבע",
    5: "חמש",
    6: "שש",
    7: "שבע",
    8: "שמונה",
    9: "תשע",
}
_ONES_MASC = {
    1: "אחד",
    2: "שניים",
    3: "שלושה",
    4: "ארבעה",
    5: "חמישה",
    6: "שישה",
    7: "שבעה",
    8: "שמונה",
    9: "תשעה",
}
_ONES_CONSTRUCT = {
    3: "שלושת",
    4: "ארבעת",
    5: "חמשת",
    6: "ששת",
    7: "שבעת",
    8: "שמונת",
    9: "תשעת",
}
_TENS = {
    2: "עשרים",
    3: "שלושים",
    4: "ארבעים",
    5: "חמישים",
    6: "שישים",
    7: "שבעים",
    8: "שמונים",
    9: "תשעים",
}
_AND = "ו"


def _under_hundred(value: int, masculine: bool) -> list[str]:
    ones = _ONES_MASC if masculine else _ONES_FEM
    if value < 10:
        return [ones[value]]
    if value == 10:
        return ["עשרה" if masculine else "עשר"]
    if 11 <= value < 20:
        if value == 12:
            teen = "שנים עשר" if masculine else "שתים עשרה"
            return [teen]
        return [ones[value - 10] + (" עשר" if masculine else " עשרה")]
    tens, unit = divmod(value, 10)
    if unit:
        return [_TENS[tens], ones[unit]]
    return [_TENS[tens]]


def _chunk(value: int, masculine: bool) -> list[str]:
    """Words for 1-999; the hundreds phrase is one element."""
    words: list[str] = []
    hundreds, rest = divmod(value, 100)
    if hundreds == 1:
        words.append("מאה")
    elif hundreds == 2:
        words.append("מאתיים")
    elif hundreds:
        words.append(f"{_ONES_FEM[hundreds]} מאות")
    if rest:
        words.extend(_under_hundred(rest, masculine))
    return words


class HebrewRenderer(LexicalRenderer):
    locale = "he"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data("he", tuple(CARDINALS["he"][i] for i in range(10)))

    def _cardinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > self.max_cardinal:
            raise InvalidValueError(
                f"{self.locale} cardinal value is outside the supported range"
            )
        if value < 0:
            return f"מינוס {self._cardinal(-value)}"
        if value == 0:
            return "אפס"
        words: list[str] = []
        millions, rest = divmod(value, 1_000_000)
        if millions:
            words.extend(self._scale_chunk(millions, "מיליון"))
            if len(words) > 1:
                words[-1] = _AND + words[-1]
        thousands, rest2 = divmod(rest, 1_000)
        if thousands:
            words.extend(self._scale_chunk(thousands, "אלף"))
            if len(words) > 1:
                words[-1] = _AND + words[-1]
        if rest2:
            words.extend(_chunk(rest2, masculine=False))
            if len(words) > 1:
                words[-1] = _AND + words[-1]
        return " ".join(words)

    def _scale_chunk(self, quotient: int, noun: str) -> list[str]:
        if noun == "אלף":
            if quotient == 1:
                return ["אלף"]
            if quotient == 2:
                return ["אלפיים"]
            if quotient == 10:
                return ["עשרת אלפים"]
            if quotient < 10:
                return [f"{_ONES_CONSTRUCT[quotient]} אלפים"]
        else:
            if quotient == 1:
                return ["מיליון"]
            if quotient == 2:
                return ["שני מיליון"]
            if quotient == 10:
                return ["עשרה מיליון"]
            if quotient < 10:
                return [f"{_ONES_MASC[quotient]} מיליון"]
        words = _chunk(quotient, masculine=True)
        words[-1] = f"{words[-1]} {noun}"
        return words

    def _decimal(self, value: object) -> str:
        if not isinstance(value, DecimalNumber):
            raise InvalidValueError("decimal form requires DecimalNumber or Decimal")
        policy = decimal_policy(self.locale)
        integer = self._cardinal(int(value.integer))
        if value.negative:
            integer = (
                f"{policy.negative_prefix}{policy.negative_separator}{integer}".strip()
            )
        fraction = policy.digit_separator.join(
            self.data.digits[int(digit)] for digit in value.fraction
        )
        return (
            f"{integer}{policy.before_marker}{policy.marker}"
            f"{policy.after_marker}{fraction}"
        )
