"""Portuguese numeral renderer."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from ..model import NumeralForm, NumeralRequest, NumeralResult, Syntax
from .base import validate_request

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
_SCALES = [(1_000_000_000_000, "bilhão"), (1_000_000, "milhão"), (1_000, "mil")]
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
            text = self._ordinal(value)
        elif request.form is NumeralForm.YEAR:
            text = self._cardinal(value)
        else:
            text = self._cardinal(value)
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
            base = _TENS[tens]
            return base + (" e " + self._under_20[units] if units else "")
        if value < 1_000:
            hundreds, remainder = divmod(value, 100)
            if hundreds == 1:
                prefix = "cem" if remainder == 0 else "cento"
            else:
                prefix = self._under_20[hundreds] + "centos"
            return prefix + (" e " + self._cardinal(remainder) if remainder else "")
        for scale, name in _SCALES:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                if scale == 1_000:
                    prefix = "mil"
                else:
                    if quotient == 1:
                        prefix = f"um {name}"
                    else:
                        prefix = f"{self._cardinal(quotient)} {name}"
                return prefix + (" e " + self._cardinal(remainder) if remainder else "")
        raise InvalidValueError(
            "Portuguese cardinal value is outside the supported range"
        )

    def _ordinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidValueError("ordinal form requires a non-negative integer")
        if value in _ORDINALS_BR:
            return _ORDINALS_BR[value]
        return self._cardinal(value) + "ésimo"

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
