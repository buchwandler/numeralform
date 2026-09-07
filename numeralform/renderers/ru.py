"""Russian numeral renderer with the v0.1 gender contract."""

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
    Syntax,
)
from .base import validate_request


_UNDER_20 = (
    "ноль",
    "один",
    "два",
    "три",
    "четыре",
    "пять",
    "шесть",
    "семь",
    "восемь",
    "девять",
    "десять",
    "одиннадцать",
    "двенадцать",
    "тринадцать",
    "четырнадцать",
    "пятнадцать",
    "шестнадцать",
    "семнадцать",
    "восемнадцать",
    "девятнадцать",
)
_UNITS = {
    None: ("ноль", "один", "два"),
    Gender.MASCULINE: ("ноль", "один", "два"),
    Gender.FEMININE: ("ноль", "одна", "две"),
    Gender.NEUTER: ("ноль", "одно", "два"),
}
_TENS = (
    "",
    "",
    "двадцать",
    "тридцать",
    "сорок",
    "пятьдесят",
    "шестьдесят",
    "семьдесят",
    "восемьдесят",
    "девяносто",
)
_HUNDREDS = (
    "",
    "сто",
    "двести",
    "триста",
    "четыреста",
    "пятьсот",
    "шестьсот",
    "семьсот",
    "восемьсот",
    "девятьсот",
)
_DIGITS = (
    "ноль",
    "один",
    "два",
    "три",
    "четыре",
    "пять",
    "шесть",
    "семь",
    "восемь",
    "девять",
)
_ORDINALS = {
    0: "нулевой",
    1: "первый",
    2: "второй",
    3: "третий",
    4: "четвёртый",
    5: "пятый",
    6: "шестой",
    7: "седьмой",
    8: "восьмой",
    9: "девятый",
    10: "десятый",
    11: "одиннадцатый",
    12: "двенадцатый",
    13: "тринадцатый",
    14: "четырнадцатый",
    15: "пятнадцатый",
    16: "шестнадцатый",
    17: "семнадцатый",
    18: "восемнадцатый",
    19: "девятнадцатый",
    20: "двадцатый",
}
_ORDINAL_GENDER = {
    (1, Gender.MASCULINE): "первый",
    (1, Gender.FEMININE): "первая",
    (1, Gender.NEUTER): "первое",
    (2, Gender.MASCULINE): "второй",
    (2, Gender.FEMININE): "вторая",
    (2, Gender.NEUTER): "второе",
}


class RussianRenderer:
    locale = "ru"

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        return LocaleCapabilities(
            forms=frozenset(NumeralForm),
            syntaxes=frozenset(
                {Syntax.STANDALONE, Syntax.ATTRIBUTIVE, Syntax.ORDINAL_ADJECTIVAL}
            ),
            genders=frozenset({Gender.MASCULINE, Gender.FEMININE, Gender.NEUTER}),
            styles=frozenset({"default"}),
            notes=(
                "Case and animacy are reserved for a future reviewed morphology contract.",
            ),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        validate_request(request, self.capabilities())
        value = request.value
        if request.form is NumeralForm.DIGITS:
            text = self._digits(value)
        elif request.form is NumeralForm.DECIMAL:
            text = self._decimal(value)
        elif request.form is NumeralForm.FRACTION:
            text = self._fraction(value)
        elif request.form is NumeralForm.ORDINAL:
            text = self._ordinal(value, request.morphology.gender)
        else:
            text = self._cardinal(value, request.morphology.gender)
        return NumeralResult(
            text, request.locale, request.form, request.style, request.morphology
        )

    def _cardinal(self, value, gender: Gender | None = None) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError("cardinal form requires an integer")
        if value < 0:
            return "минус " + self._cardinal(-value, gender)
        return self._under(value, gender)

    def _under(self, value: int, gender: Gender | None = None) -> str:
        if value < 20:
            if value in (1, 2):
                return _UNITS[gender][value]
            return _UNDER_20[value]
        if value < 100:
            tens, units = divmod(value, 10)
            return _TENS[tens] + (f" {_UNITS[gender][units]}" if units else "")
        if value < 1000:
            hundreds, remainder = divmod(value, 100)
            return _HUNDREDS[hundreds] + (
                f" {self._under(remainder, gender)}" if remainder else ""
            )
        if value < 1_000_000:
            thousands, remainder = divmod(value, 1000)
            prefix = (
                self._under(thousands, Gender.FEMININE) + " тысяча"
                if thousands == 1
                else self._under(thousands, Gender.FEMININE) + " тысячи"
                if 2 <= thousands % 10 <= 4 and not 12 <= thousands % 100 <= 14
                else self._under(thousands, Gender.FEMININE) + " тысяч"
            )
            return prefix + (f" {self._under(remainder, gender)}" if remainder else "")
        millions, remainder = divmod(value, 1_000_000)
        if millions == 1:
            prefix = "один миллион"
        elif 2 <= millions % 10 <= 4 and not 12 <= millions % 100 <= 14:
            prefix = f"{self._under(millions)} миллиона"
        else:
            prefix = f"{self._under(millions)} миллионов"
        return prefix + (f" {self._under(remainder, gender)}" if remainder else "")

    def _digits(self, value) -> str:
        if isinstance(value, DigitSequence):
            digits, negative = value.digits, False
        elif isinstance(value, int) and not isinstance(value, bool):
            negative, digits = value < 0, str(abs(value))
        else:
            raise TypeError("digits form requires an integer or DigitSequence")
        return ("минус " if negative else "") + " ".join(
            _DIGITS[int(digit)] for digit in digits
        )

    def _decimal(self, value) -> str:
        if not isinstance(value, DecimalNumber):
            raise TypeError("decimal form requires DecimalNumber or Decimal")
        sign = "минус " if value.negative else ""
        fraction = " ".join(_DIGITS[int(digit)] for digit in value.fraction)
        return f"{sign}{self._under(int(value.integer))} точка {fraction}"

    def _ordinal(self, value, gender: Gender | None = None) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise TypeError("ordinal form requires a non-negative integer")
        if (value, gender) in _ORDINAL_GENDER:
            return _ORDINAL_GENDER[(value, gender)]
        if value in _ORDINALS:
            return _ORDINALS[value]
        if value < 100:
            tens, units = divmod(value, 10)
            return (
                f"{_TENS[tens]} {self._ordinal(units, gender)}"
                if units
                else self._ordinal(tens * 10, gender)
            )
        hundreds, remainder = divmod(value, 100)
        return f"{self._under(hundreds * 100)}{f' {self._ordinal(remainder, gender)}' if remainder else ' сотый'}"

    def _fraction(self, value) -> str:
        if not isinstance(value, FractionNumber):
            raise TypeError("fraction form requires FractionNumber or Fraction")
        names = {
            2: "вторая",
            3: "третья",
            4: "четвёртая",
            5: "пятая",
            6: "шестая",
            7: "седьмая",
            8: "восьмая",
            9: "девятая",
            10: "десятая",
        }
        denominator = names.get(
            value.denominator, self._ordinal(value.denominator, Gender.FEMININE)
        )
        if value.numerator < 0:
            return "минус " + self._fraction(
                FractionNumber(-value.numerator, value.denominator)
            )
        numerator = self._under(
            value.numerator, Gender.FEMININE if value.numerator == 1 else None
        )
        return f"{numerator} {denominator}"
