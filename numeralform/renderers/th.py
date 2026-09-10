"""Thai numeral renderer."""

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
    "ศูนย์",
    "หนึ่ง",
    "สอง",
    "สาม",
    "สี่",
    "ห้า",
    "หก",
    "เจ็ด",
    "แปด",
    "เก้า",
)
_TENS = ("", "สิบ", "ยี่สิบ", "สามสิบ", "สี่สิบ", "ห้าสิบ", "หกสิบ", "เจ็ดสิบ", "แปดสิบ", "เก้าสิบ")
_MAX_CARDINAL = 999_999_999_999


class ThaiRenderer:
    locale = "th"

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
                "Thai uses context-sensitive one forms: เอ็ด (after hundreds/thousands at unit position), หนึ่ง (standalone/leading).",
                "Tens use ยี่ for 20. No spaces between components.",
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

    def _under_million(self, value: int, *, trailing_one: bool = False) -> str:
        if value < 10:
            if value == 1 and trailing_one:
                return "เอ็ด"
            return _UNDER_10[value]
        if value < 20:
            units = value % 10
            return (
                "สิบ"
                if units == 0
                else "สิบเอ็ด"
                if units == 1
                else f"สิบ{_UNDER_10[units]}"
            )
        if value < 100:
            tens, units = divmod(value, 10)
            base = _TENS[tens]
            return (
                base
                if units == 0
                else f"{base}{'เอ็ด' if units == 1 else _UNDER_10[units]}"
            )
        for scale, name in (
            (100_000, "แสน"),
            (10_000, "หมื่น"),
            (1_000, "พัน"),
            (100, "ร้อย"),
        ):
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                text = f"{self._under_million(quotient)}{name}"
                if remainder:
                    text += self._under_million(remainder, trailing_one=True)
                return text
        raise InvalidValueError("Thai value is outside the under-million range")

    def _render_cardinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > _MAX_CARDINAL:
            raise InvalidValueError(
                "Thai cardinal supports integers from -999999999999 through 999999999999"
            )
        if value < 0:
            return "ติดลบ" + self._render_cardinal(-value)
        if value == 0:
            return "ศูนย์"
        high, low = divmod(value, 1_000_000)
        if high == 0:
            return self._under_million(low)
        text = f"{self._render_cardinal(high)}ล้าน"
        return text if low == 0 else text + self._under_million(low, trailing_one=True)

    def _render_digits(self, value) -> str:
        from ..model import DigitSequence

        if isinstance(value, DigitSequence):
            digits = value.digits
        elif isinstance(value, int) and not isinstance(value, bool):
            digits = str(abs(value))
        else:
            raise InvalidValueError("digits form requires an integer or DigitSequence")
        return " ".join(_UNDER_10[int(d)] for d in digits)


__all__ = ["ThaiRenderer"]
