"""Korean numeral renderer."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from ..model import (
    NumeralForm,
    NumeralRequest,
    NumeralResult,
)
from .base import require_int, validate_request

_DIGITS = (
    "영",
    "일",
    "이",
    "삼",
    "사",
    "오",
    "육",
    "칠",
    "팔",
    "구",
)
_SCALES = [
    (1_0000_0000_0000, "조"),
    (1_0000_0000, "억"),
    (1_0000, "만"),
    (1_000, "천"),
    (100, "백"),
    (10, "십"),
]
_MAX_CARDINAL = 9999_9999_9999


class KoreanRenderer:
    locale = "ko"

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
                "Korean Sino-Korean numbers use multiplicative composition.",
                "백, 십 omit leading 일. Native counters stay in Spokenform.",
            ),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        validate_request(request, self.capabilities())
        value = request.value
        if request.form is NumeralForm.DIGITS:
            text = self._render_digits(value)
        elif request.form is NumeralForm.YEAR:
            text = self._render_cardinal(require_int(value)) + "년"
        else:
            text = self._render_cardinal(require_int(value))
        return NumeralResult(
            text, request.locale, request.form, request.style, request.morphology
        )

    def _render_cardinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > _MAX_CARDINAL:
            raise InvalidValueError(
                "Korean cardinal supports integers from -999999999999 through 999999999999"
            )
        if value < 0:
            return "마이너스" + self._render_cardinal(-value)
        if value == 0:
            return "영"
        if value < 10:
            return _DIGITS[value]
        parts: list[str] = []
        for scale, name in _SCALES:
            if value >= scale:
                quotient, value = divmod(value, scale)
                if scale >= 1_0000:
                    parts.append(self._render_cardinal(quotient) + name)
                else:
                    # 천, 백, 십 omit leading 일
                    parts.append(("" if quotient == 1 else _DIGITS[quotient]) + name)
        if value > 0:
            parts.append(_DIGITS[value])
        return "".join(parts)

    def _render_digits(self, value) -> str:
        from ..model import DigitSequence

        if isinstance(value, DigitSequence):
            digits = value.digits
        elif isinstance(value, int) and not isinstance(value, bool):
            digits = str(abs(value))
        else:
            raise InvalidValueError("digits form requires an integer or DigitSequence")
        return " ".join(_DIGITS[int(d)] for d in digits)


__all__ = ["KoreanRenderer"]
