"""Russian numeral renderer with a deliberately bounded morphology contract."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities
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
    "ноль", "один", "два", "три", "четыре", "пять", "шесть", "семь",
    "восемь", "девять", "десять", "одиннадцать", "двенадцать", "тринадцать",
    "четырнадцать", "пятнадцать", "шестнадцать", "семнадцать", "восемнадцать",
    "девятнадцать",
)
_UNITS = {
    None: ("ноль", "один", "два"),
    Gender.MASCULINE: ("ноль", "один", "два"),
    Gender.FEMININE: ("ноль", "одна", "две"),
    Gender.NEUTER: ("ноль", "одно", "два"),
}
_TENS = ("", "", "двадцать", "тридцать", "сорок", "пятьдесят", "шестьдесят", "семьдесят", "восемьдесят", "девяносто")
_HUNDREDS = ("", "сто", "двести", "триста", "четыреста", "пятьсот", "шестьсот", "семьсот", "восемьсот", "девятьсот")
_DIGITS = ("ноль", "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять")
_ORDINALS = {
    0: "нулевой", 1: "первый", 2: "второй", 3: "третий", 4: "четвёртый",
    5: "пятый", 6: "шестой", 7: "седьмой", 8: "восьмой", 9: "девятый",
    10: "десятый", 11: "одиннадцатый", 12: "двенадцатый", 13: "тринадцатый",
    14: "четырнадцатый", 15: "пятнадцатый", 16: "шестнадцатый",
    17: "семнадцатый", 18: "восемнадцатый", 19: "девятнадцатый", 20: "двадцатый",
}
_ORDINAL_GENDER = {
    (1, Gender.MASCULINE): "первый", (1, Gender.FEMININE): "первая", (1, Gender.NEUTER): "первое",
    (2, Gender.MASCULINE): "второй", (2, Gender.FEMININE): "вторая", (2, Gender.NEUTER): "второе",
}
_FRACTION_SINGULAR = {
    2: "вторая", 3: "третья", 4: "четвёртая", 5: "пятая", 6: "шестая",
    7: "седьмая", 8: "восьмая", 9: "девятая", 10: "десятая",
}
_FRACTION_PLURAL = {
    2: "вторых", 3: "третьих", 4: "четвёртых", 5: "пятых", 6: "шестых",
    7: "седьмых", 8: "восьмых", 9: "девятых", 10: "десятых",
}
_MAX_CARDINAL = 999_999_999
_MAX_ORDINAL = 29
_MAX_FRACTION_DENOMINATOR = 10


class RussianRenderer:
    locale = "ru"

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        return LocaleCapabilities(
            profiles=(
                CapabilityProfile(
                    NumeralForm.CARDINAL,
                    syntaxes=frozenset({Syntax.STANDALONE, Syntax.ATTRIBUTIVE}),
                    genders=frozenset({Gender.MASCULINE, Gender.FEMININE, Gender.NEUTER}),
                ),
                CapabilityProfile(NumeralForm.DIGITS),
                CapabilityProfile(NumeralForm.DECIMAL),
                CapabilityProfile(NumeralForm.FRACTION),
                CapabilityProfile(
                    NumeralForm.ORDINAL,
                    syntaxes=frozenset({Syntax.STANDALONE, Syntax.ORDINAL_ADJECTIVAL}),
                ),
                CapabilityProfile(NumeralForm.YEAR),
            ),
            notes=(
                "Case and animacy are reserved for a future reviewed morphology contract.",
                "Russian cardinal support is bounded below one billion.",
                "Ordinal and fraction ranges are deliberately reviewed and finite.",
                "Year follows explicit cardinal semantics for Russian.",
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
        return NumeralResult(text, request.locale, request.form, request.style, request.morphology)

    def _cardinal(self, value: int, gender: Gender | None = None) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > _MAX_CARDINAL:
            raise InvalidValueError("Russian cardinal supports magnitudes below 1000000000")
        if value < 0:
            return "минус " + self._cardinal(-value, gender)
        if value < 1000:
            return self._under(value, gender)
        if value < 1_000_000:
            group, remainder = divmod(value, 1000)
            text = f"{self._under(group, Gender.FEMININE)} {self._scale_word(group, 'thousand')}"
        else:
            group, remainder = divmod(value, 1_000_000)
            text = f"{self._under(group, Gender.MASCULINE)} {self._scale_word(group, 'million')}"
        if remainder:
            text += f" {self._cardinal(remainder, gender)}"
        return text

    @staticmethod
    def _scale_word(value: int, scale: str) -> str:
        category = plural_category(value)
        forms = {
            "thousand": {"one": "тысяча", "few": "тысячи", "many": "тысяч"},
            "million": {"one": "миллион", "few": "миллиона", "many": "миллионов"},
        }
        return forms[scale][category]

    def _under(self, value: int, gender: Gender | None = None) -> str:
        if value < 20:
            if value in (1, 2):
                return _UNITS[gender][value]
            return _UNDER_20[value]
        if value < 100:
            tens, units = divmod(value, 10)
            unit_text = _UNITS[gender][units] if units in (1, 2) else _UNDER_20[units]
            return _TENS[tens] + (f" {unit_text}" if units else "")
        hundreds, remainder = divmod(value, 100)
        return _HUNDREDS[hundreds] + (f" {self._under(remainder, gender)}" if remainder else "")

    def _digits(self, value) -> str:
        if isinstance(value, DigitSequence):
            digits, negative = value.digits, False
        elif isinstance(value, int) and not isinstance(value, bool):
            negative, digits = value < 0, str(abs(value))
        else:
            raise InvalidValueError("digits form requires an integer or DigitSequence")
        return ("минус " if negative else "") + " ".join(_DIGITS[int(digit)] for digit in digits)

    def _decimal(self, value) -> str:
        if not isinstance(value, DecimalNumber):
            raise InvalidValueError("decimal form requires DecimalNumber or Decimal")
        if int(value.integer) > _MAX_CARDINAL:
            raise InvalidValueError("Russian decimal integer part is outside the supported range")
        sign = "минус " if value.negative else ""
        fraction = " ".join(_DIGITS[int(digit)] for digit in value.fraction)
        return f"{sign}{self._under(int(value.integer))} точка {fraction}"

    def _ordinal(self, value: int, gender: Gender | None = None) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidValueError("ordinal form requires a non-negative integer")
        if value > _MAX_ORDINAL:
            raise InvalidValueError("Russian ordinal is supported only for values 0 through 29")
        if (value, gender) in _ORDINAL_GENDER:
            return _ORDINAL_GENDER[(value, gender)]
        if value in _ORDINALS:
            return _ORDINALS[value]
        tens, units = divmod(value, 10)
        return f"{_TENS[tens]} {self._ordinal(units, gender)}"

    def _fraction(self, value) -> str:
        if not isinstance(value, FractionNumber):
            raise InvalidValueError("fraction form requires FractionNumber or Fraction")
        if abs(value.numerator) > _MAX_CARDINAL or value.denominator > _MAX_FRACTION_DENOMINATOR:
            raise InvalidValueError("Russian fraction is outside the reviewed range")
        if value.numerator < 0:
            return "минус " + self._fraction(FractionNumber(-value.numerator, value.denominator))
        numerator = self._under(value.numerator, Gender.FEMININE if value.numerator == 1 else None)
        denominator = (
            _FRACTION_SINGULAR[value.denominator]
            if value.numerator == 1
            else _FRACTION_PLURAL[value.denominator]
        )
        return f"{numerator} {denominator}"


def plural_category(value: int) -> str:
    """Return the Russian one/few/many category for a scale group."""
    n100 = abs(value) % 100
    n10 = abs(value) % 10
    if 11 <= n100 <= 14:
        return "many"
    if n10 == 1:
        return "one"
    if 2 <= n10 <= 4:
        return "few"
    return "many"
