"""Spanish numeral renderer."""

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
    "cero",
    "uno",
    "dos",
    "tres",
    "cuatro",
    "cinco",
    "seis",
    "siete",
    "ocho",
    "nueve",
    "diez",
    "once",
    "doce",
    "trece",
    "catorce",
    "quince",
    "dieciséis",
    "diecisiete",
    "dieciocho",
    "diecinueve",
)
_TWENTIES = {
    20: "veinte",
    21: "veintiuno",
    22: "veintidós",
    23: "veintitrés",
    24: "veinticuatro",
    25: "veinticinco",
    26: "veintiséis",
    27: "veintisiete",
    28: "veintiocho",
    29: "veintinueve",
}
_TENS = {
    30: "treinta",
    40: "cuarenta",
    50: "cincuenta",
    60: "sesenta",
    70: "setenta",
    80: "ochenta",
    90: "noventa",
}
_HUNDREDS = {
    100: "cien",
    200: "doscientos",
    300: "trescientos",
    400: "cuatrocientos",
    500: "quinientos",
    600: "seiscientos",
    700: "setecientos",
    800: "ochocientos",
    900: "novecientos",
}
_DIGITS = _UNDER_20[:10]
_ORDINALS = {
    0: "cero",
    1: "primero",
    2: "segundo",
    3: "tercero",
    4: "cuarto",
    5: "quinto",
    6: "sexto",
    7: "séptimo",
    8: "octavo",
    9: "noveno",
    10: "décimo",
    11: "undécimo",
    12: "duodécimo",
    13: "decimotercero",
    14: "decimocuarto",
    15: "decimoquinto",
    16: "decimosexto",
    17: "decimoséptimo",
    18: "decimoctavo",
    19: "decimonoveno",
    20: "vigésimo",
}


class SpanishRenderer:
    locale = "es"

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        return LocaleCapabilities(
            forms=frozenset(NumeralForm),
            syntaxes=frozenset(
                {Syntax.STANDALONE, Syntax.ATTRIBUTIVE, Syntax.ORDINAL_ADJECTIVAL}
            ),
            genders=frozenset({Gender.MASCULINE, Gender.FEMININE}),
            styles=frozenset({"default"}),
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
            text = self._ordinal(value, request)
        elif request.form is NumeralForm.YEAR:
            text = self._cardinal(value, request)
        else:
            text = self._cardinal(value, request)
        return NumeralResult(
            text, request.locale, request.form, request.style, request.morphology
        )

    def _cardinal(self, value, request: NumeralRequest) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError("cardinal form requires an integer")
        if value < 0:
            return "menos " + self._cardinal(-value, request)
        text = self._cardinal_plain(value)
        if request.syntax is Syntax.ATTRIBUTIVE and request.morphology.gender in (
            Gender.MASCULINE,
            Gender.FEMININE,
        ):
            if value == 1 or text.endswith("uno"):
                if request.morphology.gender is Gender.FEMININE:
                    ending = "una"
                elif value == 21:
                    ending = "ún"
                else:
                    ending = "un"
                text = text[:-3] + ending
        return text

    def _cardinal_plain(self, value: int) -> str:
        if value < 20:
            return _UNDER_20[value]
        if value < 30:
            return _TWENTIES[value]
        if value < 100:
            tens, units = divmod(value, 10)
            return _TENS[tens * 10] + (f" y {_UNDER_20[units]}" if units else "")
        if value < 1000:
            hundreds, remainder = divmod(value, 100)
            prefix = _HUNDREDS[hundreds * 100]
            if value == 100:
                return prefix
            if hundreds == 1:
                prefix = "ciento"
            return prefix + (f" {_cardinal_plain(remainder)}" if remainder else "")
        if value < 1_000_000:
            thousands, remainder = divmod(value, 1000)
            prefix = "mil" if thousands == 1 else f"{_cardinal_plain(thousands)} mil"
            return prefix + (f" {_cardinal_plain(remainder)}" if remainder else "")
        millions, remainder = divmod(value, 1_000_000)
        prefix = (
            "un millón" if millions == 1 else f"{_cardinal_plain(millions)} millones"
        )
        return prefix + (f" {_cardinal_plain(remainder)}" if remainder else "")

    def _digits(self, value) -> str:
        if isinstance(value, DigitSequence):
            digits = value.digits
            negative = False
        elif isinstance(value, int) and not isinstance(value, bool):
            negative = value < 0
            digits = str(abs(value))
        else:
            raise TypeError("digits form requires an integer or DigitSequence")
        return ("menos " if negative else "") + " ".join(
            _DIGITS[int(digit)] for digit in digits
        )

    def _decimal(self, value) -> str:
        if not isinstance(value, DecimalNumber):
            raise TypeError("decimal form requires DecimalNumber or Decimal")
        sign = "menos " if value.negative else ""
        integer = self._cardinal_plain(int(value.integer))
        fraction = " ".join(_DIGITS[int(digit)] for digit in value.fraction)
        return f"{sign}{integer} punto {fraction}"

    def _ordinal(self, value, request: NumeralRequest) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise TypeError("ordinal form requires a non-negative integer")
        if value in _ORDINALS:
            text = _ORDINALS[value]
        elif value < 100:
            tens, units = divmod(value, 10)
            text = (
                f"{_ORDINALS[tens * 10]} {_ORDINALS[units]}"
                if units
                else _ORDINALS[tens * 10]
            )
        else:
            hundreds, remainder = divmod(value, 100)
            text = f"{self._cardinal_plain(hundreds * 100)}{f' {self._ordinal(remainder, request)}' if remainder else ''}"
        if request.morphology.gender is Gender.FEMININE:
            if text.endswith("primero"):
                text = text[:-7] + "primera"
            elif text.endswith("tercero"):
                text = text[:-7] + "tercera"
        elif (
            request.syntax is Syntax.ATTRIBUTIVE
            and request.morphology.gender is Gender.MASCULINE
        ):
            if text.endswith("primero"):
                text = text[:-7] + "primer"
            elif text.endswith("tercero"):
                text = text[:-7] + "tercer"
        return text

    def _fraction(self, value) -> str:
        if not isinstance(value, FractionNumber):
            raise TypeError("fraction form requires FractionNumber or Fraction")
        names = {
            2: "medio",
            3: "tercio",
            4: "cuarto",
            5: "quinto",
            6: "sexto",
            7: "séptimo",
            8: "octavo",
            9: "noveno",
            10: "décimo",
        }
        denominator = names.get(
            value.denominator, self._ordinal(value.denominator, NumeralRequest(0, "es"))
        )
        if value.numerator < 0:
            return "menos " + self._fraction(
                FractionNumber(-value.numerator, value.denominator)
            )
        if value.numerator == 1:
            return f"un {denominator}"
        if denominator.endswith("o"):
            denominator += "s"
        return f"{self._cardinal_plain(value.numerator)} {denominator}"


def _cardinal_plain(value: int) -> str:
    return SpanishRenderer._cardinal_plain(SpanishRenderer, value)
