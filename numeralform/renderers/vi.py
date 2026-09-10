"""Vietnamese numeral renderer."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from ..model import (
    NumeralForm,
    NumeralRequest,
    NumeralResult,
)
from .base import validate_request

_UNDER_10 = (
    "không",
    "một",
    "hai",
    "ba",
    "bốn",
    "năm",
    "sáu",
    "bảy",
    "tám",
    "chín",
)
_TENS = (
    "",
    "mười",
    "hai mươi",
    "ba mươi",
    "bốn mươi",
    "năm mươi",
    "sáu mươi",
    "bảy mươi",
    "tám mươi",
    "chín mươi",
)
_SCALES = [
    (1_000_000_000, "tỷ"),
    (1_000_000, "triệu"),
    (1_000, "nghìn"),
]
_MAX_CARDINAL = 999_999_999_999


class VietnameseRenderer:
    locale = "vi"

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        return LocaleCapabilities(
            profiles=(
                CapabilityProfile(
                    NumeralForm.CARDINAL,
                    domain=NumericDomain(maximum=_MAX_CARDINAL),
                ),
                CapabilityProfile(NumeralForm.DIGITS),
                CapabilityProfile(NumeralForm.YEAR),
            ),
            notes=(
                "Vietnamese uses contextual variants mốt (1 after tens) and lăm (5 after tens).",
                "Ordinal rendering uses cardinal with context from Spokenform.",
            ),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        validate_request(request, self.capabilities())
        value = request.value
        if request.form is NumeralForm.DIGITS:
            text = self._render_digits(value)
        elif request.form is NumeralForm.YEAR:
            text = self._render_cardinal(value)
        else:
            text = self._render_cardinal(value)
        return NumeralResult(
            text, request.locale, request.form, request.style, request.morphology
        )

    def _render_cardinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > _MAX_CARDINAL:
            raise InvalidValueError(
                "Vietnamese cardinal supports integers from -999999999999 through 999999999999"
            )
        if value < 0:
            return "âm " + self._render_cardinal(-value)
        if value == 0:
            return "không"
        if value < 10:
            return _UNDER_10[value]
        if value < 20:
            units = value % 10
            if units == 0:
                return "mười"
            if units == 1:
                return "mười một"
            if units == 5:
                return "mười lăm"
            return f"mười {_UNDER_10[units]}"
        if value < 100:
            tens, units = divmod(value, 10)
            base = _TENS[tens]
            if units == 0:
                return base
            if units == 1:
                return f"{base} mốt"
            if units == 5:
                return f"{base} lăm"
            return f"{base} {_UNDER_10[units]}"
        if value < 1_000:
            hundreds, remainder = divmod(value, 100)
            base = f"{_UNDER_10[hundreds]} trăm"
            if remainder == 0:
                return base
            if remainder < 10:
                return f"{base} lẻ {_UNDER_10[remainder]}"
            return f"{base} {self._render_cardinal(remainder)}"
        for scale, name in _SCALES:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                base = f"{self._render_cardinal(quotient)} {name}"
                if remainder == 0:
                    return base
                if remainder < 10:
                    return f"{base} lẻ {_UNDER_10[remainder]}"
                return f"{base} {self._render_cardinal(remainder)}"
        raise InvalidValueError(
            "Vietnamese cardinal value is outside the supported range"
        )

    def _render_digits(self, value) -> str:
        from ..model import DigitSequence

        if isinstance(value, DigitSequence):
            digits = value.digits
        elif isinstance(value, int) and not isinstance(value, bool):
            digits = str(abs(value))
        else:
            raise InvalidValueError("digits form requires an integer or DigitSequence")
        return " ".join(_UNDER_10[int(d)] for d in digits)


__all__ = ["VietnameseRenderer"]
