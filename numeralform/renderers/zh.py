"""Canonical Chinese numeral rendering shared by Chinese regional locales."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..model import DigitSequence
from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data

_DIGITS = ("零", "一", "二", "三", "四", "五", "六", "七", "八", "九")
_UNITS = ((1000, "千"), (100, "百"), (10, "十"))


class ChineseRenderer(LexicalRenderer):
    locale = "zh"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(locale, _DIGITS, compound="", negative="负", ordinal_prefix="第")

    def _cardinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > self.max_cardinal:
            raise InvalidValueError(
                "Chinese cardinal value is outside the supported range"
            )
        if value < 0:
            return "负" + self._cardinal(-value)
        if value in self.cardinals:
            return self.cardinals[value]
        return self._chinese(value)

    def _chinese_under_10000(self, value: int) -> str:
        if value == 0:
            return ""
        parts: list[str] = []
        remainder = value
        pending_zero = False
        for unit, name in _UNITS:
            digit, remainder = divmod(remainder, unit)
            if digit:
                if pending_zero and parts:
                    parts.append("零")
                if not (unit == 10 and digit == 1 and not parts):
                    parts.append(_DIGITS[digit])
                parts.append(name)
                pending_zero = False
            elif parts and remainder:
                pending_zero = True
        if remainder:
            if pending_zero and parts:
                parts.append("零")
            parts.append(_DIGITS[remainder])
        return "".join(parts)

    def _chinese(self, value: int) -> str:
        if value < 10_000:
            return self._chinese_under_10000(value)
        if value < 100_000_000:
            high, low = divmod(value, 10_000)
            text = self._chinese(high) + "万"
            if low:
                if low < 1000:
                    text += "零"
                text += self._chinese_under_10000(low)
            return text
        high, low = divmod(value, 100_000_000)
        text = self._chinese(high) + "亿"
        if low:
            if low < 10_000_000:
                text += "零"
            text += self._chinese(low)
        return text

    def _digits(self, value: object) -> str:
        if isinstance(value, DigitSequence):
            return " ".join(_DIGITS[int(digit)] for digit in value.digits)
        return super()._digits(value)

    def _year(self, value: int) -> str:
        if value < 0 or value > 9999:
            raise InvalidValueError("Chinese year value is outside the supported range")
        return "".join(_DIGITS[int(digit)] for digit in f"{value:04d}") + "年"


class ChineseRegionalRenderer(ChineseRenderer):
    """Exact regional registration with the shared documented policy."""

    def __init__(self, locale: str):
        self.region = locale


__all__ = ["ChineseRegionalRenderer", "ChineseRenderer"]
