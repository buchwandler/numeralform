"""Independent Chinese behavior for the pinned compatibility profile."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from numeralform.model import DecimalNumber

_DIGITS = "零一二三四五六七八九"
_SMALL_UNITS = ("", "十", "百", "千")


def _under_10000(value: int) -> str:
    parts: list[str] = []
    zero = False
    for position in range(3, -1, -1):
        digit, value = divmod(value, 10**position)
        if digit:
            if zero and parts:
                parts.append("零")
            if not (position == 1 and digit == 1 and not parts):
                parts.append(_DIGITS[digit])
            if position:
                parts.append(_SMALL_UNITS[position])
            zero = False
        elif parts and value:
            zero = True
    return "".join(parts) or _DIGITS[0]


def cardinal(value: int) -> str:
    if value < 0:
        return "负" + cardinal(-value)
    if value < 10_000:
        return _under_10000(value)
    if value < 100_000_000:
        high, rest = divmod(value, 10_000)
        result = cardinal(high) + "万"
        if rest:
            if rest < 1000:
                result += "零"
            result += _under_10000(rest)
        return result
    high, rest = divmod(value, 100_000_000)
    result = cardinal(high) + "亿"
    if rest:
        if rest < 10_000_000:
            result += "零"
        result += cardinal(rest)
    return result


def _decimal(value: DecimalNumber) -> str:
    sign = "負" if value.negative else ""
    fraction = value.fraction.rstrip("0")
    if not fraction:
        return sign + cardinal(int(value.integer))
    return (
        sign
        + cardinal(int(value.integer))
        + "點"
        + "".join(_DIGITS[int(digit)] for digit in fraction)
    )


def year(value: int) -> str:
    if 0 <= value < 10:
        return cardinal(value) + "年"
    sign = "負" if value < 0 else ""
    return sign + "".join(_DIGITS[int(digit)] for digit in str(abs(value))) + "年"


def render(value: object, *, form: str, **options: object) -> str:
    del options
    if form == "year":
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError("year requires an integer")
        return year(value)
    if form == "ordinal_num":
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError("ordinal_num requires an integer")
        return f"第{value}"
    if form == "currency":
        if isinstance(value, DecimalNumber):
            amount = Decimal(
                ("-" if value.negative else "") + value.integer + "." + value.fraction
            )
        elif isinstance(value, int) and not isinstance(value, bool):
            amount = Decimal(value)
        else:
            raise TypeError("number must be numeric")
        amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        negative = amount < 0
        amount = abs(amount)
        units = int(amount)
        cents = int((amount - units) * 100)
        result = ("負" if negative else "") + cardinal(units) + "元"
        if cents:
            tenths, ones = divmod(cents, 10)
            if tenths:
                result += cardinal(tenths) + "角"
            if ones:
                result += ("零" if not tenths else "") + cardinal(ones) + "分"
        return result
    if isinstance(value, DecimalNumber):
        if form == "cardinal":
            return _decimal(value)
        raise NotImplementedError()
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("number must be numeric")
    if form == "cardinal":
        return cardinal(value)
    if form == "ordinal":
        return "第" + cardinal(value)
    raise NotImplementedError()


render_zh = render
