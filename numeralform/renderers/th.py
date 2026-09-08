"""Thai numeral renderer."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities
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
_SCALES = [
    (1_000_000_000_000, "ล้านล้าน"),
    (1_000_000, "ล้าน"),
    (1_000, "พัน"),
    (100, "ร้อย"),
]
_MAX_CARDINAL = 999_999_999_999


class ThaiRenderer:
    locale = "th"

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        return LocaleCapabilities(
            profiles=(
                CapabilityProfile(NumeralForm.CARDINAL),
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

    def _render_cardinal(self, value: int, *, trailing_one: bool = False) -> str:
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
        if value < 10:
            # Context-sensitive one: เอ็ด when trailing after scales, หนึ่ง standalone
            if value == 1 and trailing_one:
                return "เอ็ด"
            return _UNDER_10[value]
        if value < 20:
            units = value % 10
            if units == 0:
                return "สิบ"
            if units == 1:
                return "สิบเอ็ด"
            return f"สิบ{_UNDER_10[units]}"
        if value < 100:
            tens, units = divmod(value, 10)
            base = _TENS[tens]
            if units == 0:
                return base
            if units == 1:
                return f"{base}เอ็ด"
            return f"{base}{_UNDER_10[units]}"
        # For larger values, use recursive composition
        for scale, name in _SCALES:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                # Leading 1 at scale position uses หนึ่ง, not เอ็ด
                if quotient == 1:
                    base = f"หนึ่ง{name}"
                else:
                    base = f"{self._render_cardinal(quotient)}{name}"
                if remainder == 0:
                    return base
                return f"{base}{self._render_cardinal(remainder, trailing_one=True)}"
        raise InvalidValueError("Thai cardinal value is outside the supported range")

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
