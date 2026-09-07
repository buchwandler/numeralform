"""Spanish numeral renderer."""

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
_HUNDREDS_FEMININE = {
    200: "doscientas",
    300: "trescientas",
    400: "cuatrocientas",
    500: "quinientas",
    600: "seiscientas",
    700: "setecientas",
    800: "ochocientas",
    900: "novecientas",
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
_MAX_CARDINAL = 999_999_999
_MAX_ORDINAL = 20
_MAX_FRACTION_DENOMINATOR = 20


class SpanishRenderer:
    locale = "es"

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        return LocaleCapabilities(
            profiles=(
                CapabilityProfile(
                    NumeralForm.CARDINAL, syntaxes=frozenset({Syntax.STANDALONE})
                ),
                CapabilityProfile(
                    NumeralForm.CARDINAL,
                    syntaxes=frozenset({Syntax.ATTRIBUTIVE}),
                    genders=frozenset({Gender.MASCULINE, Gender.FEMININE}),
                ),
                CapabilityProfile(NumeralForm.DIGITS),
                CapabilityProfile(NumeralForm.DECIMAL),
                CapabilityProfile(NumeralForm.FRACTION),
                CapabilityProfile(
                    NumeralForm.ORDINAL,
                    syntaxes=frozenset({Syntax.STANDALONE, Syntax.ORDINAL_ADJECTIVAL}),
                ),
                CapabilityProfile(
                    NumeralForm.ORDINAL,
                    syntaxes=frozenset({Syntax.ATTRIBUTIVE}),
                    genders=frozenset({Gender.MASCULINE, Gender.FEMININE}),
                ),
                CapabilityProfile(NumeralForm.YEAR),
            ),
            notes=(
                "Cardinal gender is supported only for attributive rendering.",
                "Ordinal and fraction ranges are deliberately reviewed and finite.",
                "Year follows explicit cardinal semantics for Spanish.",
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
            text = self._ordinal(value, request)
        elif request.form is NumeralForm.YEAR:
            text = self._cardinal(value, request)
        else:
            text = self._cardinal(value, request)
        return NumeralResult(
            text, request.locale, request.form, request.style, request.morphology
        )

    def _cardinal(self, value: int, request: NumeralRequest) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > _MAX_CARDINAL:
            raise InvalidValueError("Spanish cardinal is outside the supported range")
        if value < 0:
            return "menos " + self._cardinal(-value, request)
        gender = (
            request.morphology.gender if request.syntax is Syntax.ATTRIBUTIVE else None
        )
        return self._cardinal_plain(value, gender=gender, scale_context=False)

    def _cardinal_plain(
        self,
        value: int,
        *,
        gender: Gender | None = None,
        scale_context: bool = False,
    ) -> str:
        feminine = gender is Gender.FEMININE
        if value < 20:
            text = _UNDER_20[value]
            return self._agree_final_one(text, feminine=feminine) if gender else text
        if value < 30:
            text = _TWENTIES[value]
            return self._agree_final_one(text, feminine=feminine) if gender else text
        if value < 100:
            tens, units = divmod(value, 10)
            text = _TENS[tens * 10]
            if units:
                unit = self._cardinal_plain(units, gender=gender)
                text += f" y {unit}"
            return text
        if value < 1000:
            hundreds, remainder = divmod(value, 100)
            if value == 100:
                return "cien"
            if hundreds == 1:
                prefix = "ciento"
            elif feminine:
                prefix = _HUNDREDS_FEMININE[hundreds * 100]
            else:
                prefix = _HUNDREDS[hundreds * 100]
            return prefix + (
                f" {self._cardinal_plain(remainder, gender=gender)}"
                if remainder
                else ""
            )
        if value < 1_000_000:
            thousands, remainder = divmod(value, 1000)
            if thousands == 1:
                prefix = "mil"
            else:
                raw_prefix = self._cardinal_plain(
                    thousands,
                    gender=None,
                    scale_context=True,
                )
                prefix = self._apocopate_component(raw_prefix) if gender else raw_prefix
                prefix += " mil"
            return prefix + (
                f" {self._cardinal_plain(remainder, gender=gender)}"
                if remainder
                else ""
            )
        millions, remainder = divmod(value, 1_000_000)
        if millions == 1:
            prefix = "un millón"
        else:
            prefix = self._cardinal_plain(
                millions,
                gender=None,
                scale_context=True,
            )
            if gender:
                prefix = self._apocopate_component(prefix)
            prefix += " millones"
        return prefix + (
            f" {self._cardinal_plain(remainder, gender=gender)}" if remainder else ""
        )

    @staticmethod
    def _agree_final_one(text: str, *, feminine: bool) -> str:
        words = text.split()
        if not words:
            return text
        if words[-1] == "uno":
            words[-1] = "una" if feminine else "un"
        elif words[-1] == "veintiuno":
            words[-1] = "veintiuna" if feminine else "veintiún"
        return " ".join(words)

    @staticmethod
    def _apocopate_component(text: str) -> str:
        """Apocopate only the final component in a scale-modifying group."""
        words = text.split()
        if words and words[-1] == "uno":
            words[-1] = "un"
        elif words and words[-1] == "veintiuno":
            words[-1] = "veintiún"
        return " ".join(words)

    def _digits(self, value) -> str:
        if isinstance(value, DigitSequence):
            digits, negative = value.digits, False
        elif isinstance(value, int) and not isinstance(value, bool):
            negative, digits = value < 0, str(abs(value))
        else:
            raise InvalidValueError("digits form requires an integer or DigitSequence")
        return ("menos " if negative else "") + " ".join(
            _DIGITS[int(digit)] for digit in digits
        )

    def _decimal(self, value) -> str:
        if not isinstance(value, DecimalNumber):
            raise InvalidValueError("decimal form requires DecimalNumber or Decimal")
        if int(value.integer) > _MAX_CARDINAL:
            raise InvalidValueError(
                "Spanish decimal integer part is outside the supported range"
            )
        sign = "menos " if value.negative else ""
        integer = self._cardinal_plain(int(value.integer))
        fraction = " ".join(_DIGITS[int(digit)] for digit in value.fraction)
        return f"{sign}{integer} punto {fraction}"

    def _ordinal(self, value: int, request: NumeralRequest) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidValueError("ordinal form requires a non-negative integer")
        if value > _MAX_ORDINAL:
            raise InvalidValueError(
                "Spanish ordinal is supported only for values 0 through 20"
            )
        text = _ORDINALS[value]
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
            raise InvalidValueError("fraction form requires FractionNumber or Fraction")
        if value.denominator > _MAX_FRACTION_DENOMINATOR:
            raise InvalidValueError(
                "Spanish fraction denominator is outside the reviewed range"
            )
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
        if value.numerator < 0:
            return "menos " + self._fraction(
                FractionNumber(-value.numerator, value.denominator)
            )
        denominator = names.get(value.denominator)
        if denominator is None:
            denominator = self._ordinal(
                value.denominator,
                NumeralRequest(0, "es", form=NumeralForm.ORDINAL),
            )
        if value.numerator == 1:
            return f"un {denominator}"
        if denominator.endswith("o"):
            denominator += "s"
        return f"{self._cardinal_plain(value.numerator)} {denominator}"
