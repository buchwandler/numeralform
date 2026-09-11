"""English numeral renderer."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from ..model import (
    DecimalNumber,
    DigitSequence,
    FractionNumber,
    NumeralForm,
    NumeralRequest,
    NumeralResult,
    Syntax,
)
from .base import require_int, validate_request

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
_MAX_CARDINAL = 999_999_999_999
_MAX_ORDINAL = _MAX_CARDINAL
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

    default_cardinal_style = "default"

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        return LocaleCapabilities(
            profiles=(
                CapabilityProfile(
                    NumeralForm.CARDINAL,
                    domain=NumericDomain(maximum=_MAX_CARDINAL),
                    syntaxes=frozenset(
                        {
                            Syntax.STANDALONE,
                            Syntax.ATTRIBUTIVE,
                            Syntax.ORDINAL_ADJECTIVAL,
                        }
                    ),
                    styles=frozenset({"default", "british-and"}),
                ),
                CapabilityProfile(
                    NumeralForm.ORDINAL,
                    syntaxes=frozenset({Syntax.STANDALONE, Syntax.ORDINAL_ADJECTIVAL}),
                ),
                CapabilityProfile(NumeralForm.DIGITS),
                CapabilityProfile(NumeralForm.DECIMAL),
                CapabilityProfile(NumeralForm.FRACTION),
                CapabilityProfile(NumeralForm.YEAR),
            ),
            notes=(
                "Default cardinal composition is locale-owned; british-and remains an explicit style.",
                "Year uses the explicit year form, not cardinal style inference.",
            ),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        validate_request(request, self.capabilities())
        value = request.value
        if request.form is NumeralForm.DIGITS:
            text = self._render_digits(value)
        elif request.form is NumeralForm.DECIMAL:
            text = self._render_decimal(value)
        elif request.form is NumeralForm.FRACTION:
            text = self._render_fraction(value)
        elif request.form is NumeralForm.ORDINAL:
            text = self._render_ordinal(require_int(value), self.default_cardinal_style)
        elif request.form is NumeralForm.YEAR:
            text = self._render_year(require_int(value))
        else:
            text = self._render_cardinal(require_int(value), request.style)
        return NumeralResult(
            text, request.locale, request.form, request.style, request.morphology
        )

    def _render_cardinal(self, value: int, style: str | None = None) -> str:
        style = self.default_cardinal_style if style in (None, "default") else style
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > _MAX_CARDINAL:
            raise InvalidValueError(
                "English cardinal supports integers from -999999999999 through 999999999999"
            )
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
                if suffix and style == "british-and" and remainder < 100:
                    suffix = "and " + suffix
                return f"{self._render_cardinal(value // scale, style)} {name}" + (
                    f" {suffix}" if suffix else ""
                )
        raise InvalidValueError("English cardinal value is outside the supported range")

    def _render_digits(self, value) -> str:
        if isinstance(value, DigitSequence):
            digits, negative = value.digits, False
        elif isinstance(value, int) and not isinstance(value, bool):
            negative, digits = value < 0, str(abs(value))
        else:
            raise InvalidValueError("digits form requires an integer or DigitSequence")
        text = " ".join(_DIGITS[int(digit)] for digit in digits)
        return ("minus " if negative else "") + text

    def _render_decimal(self, value) -> str:
        if not isinstance(value, DecimalNumber):
            raise InvalidValueError("decimal form requires DecimalNumber or Decimal")
        if int(value.integer) > _MAX_CARDINAL:
            raise InvalidValueError(
                "English decimal integer part is outside the supported range"
            )
        prefix = "minus " if value.negative else ""
        integer = self._render_cardinal(int(value.integer), self.default_cardinal_style)
        fraction = " ".join(_DIGITS[int(digit)] for digit in value.fraction)
        return f"{prefix}{integer} point {fraction}"

    def _render_ordinal(self, value: int, style: str | None = None) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidValueError("ordinal form requires a non-negative integer")
        if value > _MAX_ORDINAL:
            raise InvalidValueError(
                "English ordinal value is outside the supported range"
            )
        if value in _ORDINALS:
            return _ORDINALS[value]
        if value < 100:
            tens, unit = divmod(value, 10)
            return f"{_TENS[tens]}-{_ORDINALS[unit]}" if unit else _ORDINALS[tens * 10]
        for scale, name in _SCALES:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                prefix = f"{self._render_cardinal(quotient, style)} {name}"
                if not remainder:
                    return prefix + "th"
                suffix = self._render_ordinal(remainder, style)
                if style == "british-and" and remainder < 100:
                    suffix = "and " + suffix
                return f"{prefix} {suffix}"
        hundreds, remainder = divmod(value, 100)
        prefix = f"{self._render_cardinal(hundreds, style)} hundred"
        if remainder:
            suffix = self._render_ordinal(remainder, style)
            if style == "british-and":
                suffix = "and " + suffix
            return prefix + f" {suffix}"
        return prefix + "th"
    def _render_fraction(self, value) -> str:
        if not isinstance(value, FractionNumber):
            raise InvalidValueError("fraction form requires FractionNumber or Fraction")
        if abs(value.numerator) > _MAX_CARDINAL or value.denominator > _MAX_ORDINAL:
            raise InvalidValueError("English fraction is outside the supported range")
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
        denominator = denominator_names.get(value.denominator)
        if denominator is None:
            denominator = self._render_ordinal(value.denominator)
        if value.numerator == 1:
            return f"one {denominator}"
        if denominator in {"half", "quarter"} or not denominator.endswith("s"):
            denominator += "s"
        return f"{self._render_cardinal(value.numerator)} {denominator}"

    def _render_year(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidValueError("year form requires a non-negative integer")
        if value > 9999:
            raise InvalidValueError("English year supports values from 0 through 9999")
        if value == 1000:
            return "one thousand"
        if 1000 <= value <= 1999:
            first, second = divmod(value, 100)
            if second == 0:
                return f"{self._render_cardinal(first)} hundred"
            if second < 10:
                return f"{self._render_cardinal(first)} oh {_SMALL[second]}"
            return f"{self._render_cardinal(first)} {self._render_cardinal(second)}"
        if value == 2000:
            return "two thousand"
        if 2001 <= value <= 2009:
            return f"two thousand {self._render_cardinal(value % 1000)}"
        if 2010 <= value <= 2099:
            return f"twenty {self._render_cardinal(value % 100)}"
        if 2100 <= value <= 9999:
            first, second = divmod(value, 100)
            if second == 0:
                return f"{self._render_cardinal(first)} hundred"
            if second < 10:
                return f"{self._render_cardinal(first)} oh {self._render_cardinal(second)}"
            return f"{self._render_cardinal(first)} {self._render_cardinal(second)}"
        return self._render_cardinal(value)
