"""Portuguese numeral renderer."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from ..model import NumeralForm, NumeralRequest, NumeralResult, Syntax
from .base import require_int, validate_request

# Brazilian and European Portuguese differences for teens
_UNDER_20_BR = (
    "zero",
    "um",
    "dois",
    "três",
    "quatro",
    "cinco",
    "seis",
    "sete",
    "oito",
    "nove",
    "dez",
    "onze",
    "doze",
    "treze",
    "catorze",
    "quinze",
    "dezesseis",
    "dezessete",
    "dezoito",
    "dezenove",
)
_UNDER_20_PT = (
    "zero",
    "um",
    "dois",
    "três",
    "quatro",
    "cinco",
    "seis",
    "sete",
    "oito",
    "nove",
    "dez",
    "onze",
    "doze",
    "treze",
    "catorze",
    "quinze",
    "dezasseis",
    "dezassete",
    "dezoito",
    "dezanove",
)
_TENS = (
    "",
    "",
    "vinte",
    "trinta",
    "quarenta",
    "cinquenta",
    "sessenta",
    "setenta",
    "oitenta",
    "noventa",
)
_ORDINALS_BR = {
    1: "primeiro",
    2: "segundo",
    3: "terceiro",
    4: "quarto",
    5: "quinto",
    6: "sexto",
    7: "sétimo",
    8: "oitavo",
    9: "nono",
    10: "décimo",
}
_ORDINALS_PT = {
    0: "zeroésimo",
    1: "primeiro",
    2: "segundo",
    3: "terceiro",
    4: "quarto",
    5: "quinto",
    6: "sexto",
    7: "sétimo",
    8: "oitavo",
    9: "nono",
    10: "décimo",
    11: "décimo primeiro",
    12: "décimo segundo",
    13: "décimo terceiro",
    14: "décimo quarto",
    15: "décimo quinto",
    16: "décimo sexto",
    17: "décimo sétimo",
    18: "décimo oitavo",
    19: "décimo nono",
    20: "vigésimo",
}
_ORDINAL_TENS_PT = {
    2: "vigésimo",
    3: "trigésimo",
    4: "quadragésimo",
    5: "quinquagésimo",
    6: "sexagésimo",
    7: "septuagésimo",
    8: "octogésimo",
    9: "nonagésimo",
}
_HUNDREDS: dict[int, str | tuple[str, str]] = {
    100: ("cem", "cento"),
    200: "duzentos",
    300: "trezentos",
    400: "quatrocentos",
    500: "quinhentos",
    600: "seiscentos",
    700: "setecentos",
    800: "oitocentos",
    900: "novecentos",
}
_MAX_CARDINAL = 999_999_999_999


class PortugueseRenderer:
    locale = "pt-BR"

    def __init__(self, variant: str = "pt-BR"):
        self._variant = variant
        self._under_20 = _UNDER_20_BR if variant == "pt-BR" else _UNDER_20_PT
        # Override locale for pt-PT
        if variant == "pt-PT":
            object.__setattr__(self, "locale", "pt-PT")

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        return LocaleCapabilities(
            profiles=(
                CapabilityProfile(
                    NumeralForm.CARDINAL,
                    domain=NumericDomain(maximum=_MAX_CARDINAL),
                ),
                CapabilityProfile(
                    NumeralForm.ORDINAL,
                    syntaxes=frozenset({Syntax.STANDALONE, Syntax.ORDINAL_ADJECTIVAL}),
                ),
                CapabilityProfile(NumeralForm.DIGITS),
                CapabilityProfile(NumeralForm.YEAR),
            ),
            notes=("Portuguese distinguishes pt-BR and pt-PT for teens.",),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        validate_request(request, self.capabilities())
        value = request.value
        if request.form is NumeralForm.DIGITS:
            text = self._digits(value)
        elif request.form is NumeralForm.ORDINAL:
            text = self._ordinal(require_int(value))
        elif request.form is NumeralForm.YEAR:
            text = self._cardinal(require_int(value))
        else:
            text = self._cardinal(require_int(value))
        return NumeralResult(
            text, request.locale, request.form, request.style, request.morphology
        )

    def _cardinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > _MAX_CARDINAL:
            raise InvalidValueError(
                "Portuguese cardinal supports integers up to 999999999999"
            )
        if value < 0:
            return "menos " + self._cardinal(-value)
        if value < 20:
            return self._under_20[value]
        if value < 100:
            tens, units = divmod(value, 10)
            return _TENS[tens] + (f" e {self._under_20[units]}" if units else "")
        if value < 1_000:
            hundreds, remainder = divmod(value, 100)
            entry = _HUNDREDS[hundreds * 100]
            if isinstance(entry, tuple):
                prefix = entry[0] if remainder == 0 else entry[1]
            else:
                prefix = entry
            return prefix + (f" e {self._cardinal(remainder)}" if remainder else "")
        scale_words = (
            (1_000_000_000, "bilhão" if self._variant == "pt-BR" else "bilião"),
            (1_000_000, "milhão"),
            (1_000, "mil"),
        )
        for scale, name in scale_words:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                if scale == 1_000:
                    prefix = (
                        "mil" if quotient == 1 else f"{self._cardinal(quotient)} mil"
                    )
                else:
                    plural_names = {
                        "milhão": "milhões",
                        "bilhão": "bilhões",
                        "bilião": "biliões",
                    }
                    scale_name = name if quotient == 1 else plural_names[name]
                    prefix = f"{self._cardinal(quotient)} {scale_name}"
                separator = (
                    " e "
                    if (
                        remainder < 100_000
                        if scale != 1_000
                        else remainder < 100 or remainder % 100 == 0
                    )
                    else " "
                )
                return prefix + (separator + self._cardinal(remainder) if remainder else "")
        raise InvalidValueError(
            "Portuguese cardinal value is outside the supported range"
        )

    def _ordinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidValueError("ordinal form requires a non-negative integer")
        if value <= 20:
            return _ORDINALS_PT[value]
        if value < 100:
            tens, units = divmod(value, 10)
            prefix = _ORDINAL_TENS_PT[tens]
            return prefix if units == 0 else f"{prefix} {self._ordinal(units)}"
        if value < 1_000:
            hundreds, remainder = divmod(value, 100)
            hundred_ordinals = {
                1: "centésimo",
                2: "ducentésimo",
                3: "trecentésimo",
                4: "quadringentésimo",
                5: "quingentésimo",
                6: "sexcentésimo",
                7: "septingentésimo",
                8: "octingentésimo",
                9: "nongentésimo",
            }
            prefix = hundred_ordinals[hundreds]
            return prefix if remainder == 0 else f"{prefix} {self._ordinal(remainder)}"
        thousands, remainder = divmod(value, 1_000)
        prefix = "milésimo" if thousands == 1 else f"{self._ordinal(thousands)} milésimo"
        return prefix if remainder == 0 else f"{prefix} {self._ordinal(remainder)}"
    def _digits(self, value) -> str:
        from ..model import DigitSequence

        if isinstance(value, DigitSequence):
            digits = value.digits
        elif isinstance(value, int) and not isinstance(value, bool):
            digits = str(abs(value))
        else:
            raise InvalidValueError("digits form requires an integer or DigitSequence")
        return " ".join(self._under_20[int(d)] for d in digits)


__all__ = ["PortugueseRenderer"]
