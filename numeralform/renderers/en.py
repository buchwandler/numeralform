"""English numeral renderer."""

from __future__ import annotations

from ..locale import LocaleCapabilities
from ..model import (
    DecimalNumber,
    DigitSequence,
    FractionNumber,
    Gender,
    NumeralForm,
    NumeralRequest,
    NumeralResult,
)
from .base import validate_request


_SMALL = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
)
_TENS = (
    "",
    "",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
)
_SCALES = ((1_000_000_000, "billion"), (1_000_000, "million"), (1_000, "thousand"))
_ORDINALS = {
    0: "zeroth",
    1: "first",
    2: "second",
    3: "third",
    4: "fourth",
    5: "fifth",
    6: "sixth",
    7: "seventh",
    8: "eighth",
    9: "ninth",
    10: "tenth",
    11: "eleventh",
    12: "twelfth",
    13: "thirteenth",
    14: "fourteenth",
    15: "fifteenth",
    16: "sixteenth",
    17: "seventeenth",
    18: "eighteenth",
    19: "nineteenth",
    20: "twentieth",
    30: "thirtieth",
    40: "fortieth",
    50: "fiftieth",
    60: "sixtieth",
    70: "seventieth",
    80: "eightieth",
    90: "ninetieth",
    100: "hundredth",
    1_000: "thousandth",
    1_000_000: "millionth",
    1_000_000_000: "billionth",
}
_DIGITS = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
)


class EnglishRenderer:
    locale = "en"

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        return LocaleCapabilities(
            forms=frozenset(NumeralForm),
            syntaxes=frozenset({"standalone", "attributive", "ordinal-adjectival"}),
            styles=frozenset({"default", "british-and", "year"}),
            notes=("Default cardinal composition omits British-style conjunctions.",),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        caps = self.capabilities()
        validate_request(request, caps)
        value = request.value
        if request.form is NumeralForm.DIGITS:
            text = self._render_digits(value)
        elif request.form is NumeralForm.DECIMAL:
            text = self._render_decimal(value)
        elif request.form is NumeralForm.FRACTION:
            text = self._render_fraction(value)
        elif request.form is NumeralForm.ORDINAL:
            text = self._render_ordinal(value)
        elif request.form is NumeralForm.YEAR:
            text = self._render_year(value)
        else:
            text = self._render_cardinal(value, request.style)
        return NumeralResult(
            text, request.locale, request.form, request.style, request.morphology
        )

    def _render_cardinal(self, value, style: str | None = None) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            if isinstance(value, DecimalNumber):
                raise TypeError("decimal values require form='decimal'")
            raise TypeError("cardinal form requires an integer")
        if value < 0:
            return "minus " + self._render_cardinal(-value, style)
        if value < 20:
            return _SMALL[value]
        if value < 100:
            return _TENS[value // 10] + (f"-{_SMALL[value % 10]}" if value % 10 else "")
        if value < 1_000:
            remainder = value % 100
            suffix = self._render_cardinal(remainder, style) if remainder else ""
            if suffix and style == "british-and":
                suffix = "and " + suffix
            return f"{_SMALL[value // 100]} hundred" + (f" {suffix}" if suffix else "")
        for scale, name in _SCALES:
            if value >= scale:
                remainder = value % scale
                suffix = self._render_cardinal(remainder, style) if remainder else ""
                return f"{self._render_cardinal(value // scale, style)} {name}" + (
                    f" {suffix}" if suffix else ""
                )
        raise AssertionError("unreachable")

    def _render_digits(self, value) -> str:
        if isinstance(value, DigitSequence):
            digits = value.digits
            negative = False
        elif isinstance(value, int) and not isinstance(value, bool):
            negative = value < 0
            digits = str(abs(value))
        else:
            raise TypeError("digits form requires an integer or DigitSequence")
        text = " ".join(_DIGITS[int(digit)] for digit in digits)
        return ("minus " if negative else "") + text

    def _render_decimal(self, value) -> str:
        if not isinstance(value, DecimalNumber):
            raise TypeError("decimal form requires DecimalNumber or Decimal")
        prefix = "minus " if value.negative else ""
        integer = self._render_cardinal(int(value.integer))
        fraction = " ".join(_DIGITS[int(digit)] for digit in value.fraction)
        return f"{prefix}{integer} point {fraction}"

    def _render_ordinal(self, value) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise TypeError("ordinal form requires a non-negative integer")
        if value in _ORDINALS:
            return _ORDINALS[value]
        if value < 100:
            tens, unit = divmod(value, 10)
            return f"{_TENS[tens]}-{_ORDINALS[unit]}" if unit else _ORDINALS[tens * 10]
        for scale, name in _SCALES:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                prefix = f"{self._render_cardinal(quotient)} {name}"
                return prefix + (
                    f" {self._render_ordinal(remainder)}" if remainder else "th"
                )
        hundreds, remainder = divmod(value, 100)
        prefix = f"{self._render_cardinal(hundreds)} hundred"
        return prefix + (f" {self._render_ordinal(remainder)}" if remainder else "th")

    def _render_fraction(self, value) -> str:
        if not isinstance(value, FractionNumber):
            raise TypeError("fraction form requires FractionNumber or Fraction")
        if value.numerator < 0:
            return "minus " + self._render_fraction(
                FractionNumber(-value.numerator, value.denominator)
            )
        denominator_names = {
            2: "half",
            3: "third",
            4: "quarter",
            5: "fifth",
            6: "sixth",
            7: "seventh",
            8: "eighth",
            9: "ninth",
            10: "tenth",
        }
        denominator = denominator_names.get(
            value.denominator, self._render_ordinal(value.denominator)
        )
        if value.numerator == 1:
            return f"one {denominator}"
        if denominator in {"half", "quarter"}:
            denominator += "s"
        elif not denominator.endswith("s"):
            denominator += "s"
        return f"{self._render_cardinal(value.numerator)} {denominator}"

    def _render_year(self, value) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise TypeError("year form requires a non-negative integer")
        if 1000 <= value <= 9999:
            first, second = divmod(value, 100)
            if second:
                return f"{self._render_cardinal(first)} {self._render_cardinal(second)}"
        return self._render_cardinal(value)
