"""Canonical Chinese numeral rendering shared by Chinese regional locales."""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import InvalidValueError
from ..locale import NumericDomain
from ..model import DecimalNumber, DigitSequence
from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data

_DIGITS = ("零", "一", "二", "三", "四", "五", "六", "七", "八", "九")
_TRADITIONAL_DIGITS = _DIGITS
_SIMPLIFIED_DIGITS = _DIGITS
_UNITS = ((1000, "千"), (100, "百"), (10, "十"))


@dataclass(frozen=True)
class ChinesePolicy:
    digits: tuple[str, ...]
    ten_thousand: str
    hundred_million: str
    negative: str
    decimal: str
    year_suffix: str


_TRADITIONAL_POLICY = ChinesePolicy(_TRADITIONAL_DIGITS, "萬", "億", "負", "點", "年")
_SIMPLIFIED_POLICY = ChinesePolicy(_SIMPLIFIED_DIGITS, "万", "亿", "负", "点", "")


class ChineseRenderer(LexicalRenderer):
    locale = "zh"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(locale, _DIGITS, compound="", negative="负")

    def __init__(self, policy: ChinesePolicy | None = None):
        self.policy = policy or _TRADITIONAL_POLICY
        self.data = locale_data(
            "zh", self.policy.digits, compound="", negative=self.policy.negative
        )

    _MAX_ORDINAL = 999_999_999

    @classmethod
    def _ordinal_domain(cls) -> NumericDomain:
        return NumericDomain(minimum=0, maximum=cls._MAX_ORDINAL, allow_negative=False)

    def _ordinal(self, value: int) -> str:
        if value < 0 or value > self._MAX_ORDINAL:
            raise InvalidValueError(
                f"{self.locale} ordinal value is outside the supported range"
            )
        return "第" + self._cardinal(value)

    def _cardinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > self.max_cardinal:
            raise InvalidValueError(
                "Chinese cardinal value is outside the supported range"
            )
        if value < 0:
            return self.policy.negative + self._cardinal(-value)
        if value in self.cardinals:
            text = self.cardinals[value]
        else:
            text = self._chinese(value)
        if self.policy.ten_thousand == "萬":
            text = text.translate(str.maketrans("万亿", "萬億"))
        return text

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
                    parts.append(self.policy.digits[0])
                if not (unit == 10 and digit == 1 and not parts):
                    parts.append(self.policy.digits[digit])
                parts.append(name)
                pending_zero = False
            elif parts and remainder:
                pending_zero = True
        if remainder:
            if pending_zero and parts:
                parts.append(self.policy.digits[0])
            parts.append(self.policy.digits[remainder])
        return "".join(parts)

    def _chinese(self, value: int) -> str:
        if value < 10_000:
            return self._chinese_under_10000(value)
        if value < 100_000_000:
            high, low = divmod(value, 10_000)
            text = self._chinese(high) + self.policy.ten_thousand
            if low:
                if low < 1000:
                    text += self.policy.digits[0]
                text += self._chinese_under_10000(low)
            return text
        high, low = divmod(value, 100_000_000)
        text = self._chinese(high) + self.policy.hundred_million
        if low:
            if low < 10_000_000:
                text += self.policy.digits[0]
            text += self._chinese(low)
        return text

    def _digits(self, value: object) -> str:
        if isinstance(value, DigitSequence):
            return " ".join(self.policy.digits[int(digit)] for digit in value.digits)
        return super()._digits(value)

    def _decimal(self, value: object) -> str:
        if not isinstance(value, DecimalNumber):
            raise InvalidValueError("decimal form requires DecimalNumber or Decimal")
        integer = self._cardinal(int(value.integer))
        if value.negative:
            integer = self.policy.negative + integer
        fraction = "".join(self.policy.digits[int(digit)] for digit in value.fraction)
        return f"{integer}{self.policy.decimal}{fraction}"

    def _year(self, value: int) -> str:
        if value < 0 or value > 9999:
            raise InvalidValueError("Chinese year value is outside the supported range")
        digits = "".join(self.policy.digits[int(digit)] for digit in str(value))
        return digits + self.policy.year_suffix


class ChineseRegionalRenderer(ChineseRenderer):
    """Exact regional registration with the shared documented policy."""

    def __init__(self, locale: str):
        self.region = locale
        policy = _SIMPLIFIED_POLICY if locale == "zh-CN" else _TRADITIONAL_POLICY
        super().__init__(policy)


__all__ = ["ChineseRegionalRenderer", "ChineseRenderer"]
