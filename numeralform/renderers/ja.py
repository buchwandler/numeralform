"""Japanese numeral renderer."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from ..model import (
    NumeralForm,
    NumeralRequest,
    NumeralResult,
    Syntax,
)
from .base import require_int, validate_request

_DIGITS = (
    "零",
    "一",
    "二",
    "三",
    "四",
    "五",
    "六",
    "七",
    "八",
    "九",
)
_SCALES = [
    (1_0000_0000_0000, "兆"),
    (1_0000_0000, "億"),
    (1_0000, "万"),
    (1_000, "千"),
    (100, "百"),
    (10, "十"),
]
_MAX_CARDINAL = 9999_9999_9999


class JapaneseRenderer:
    locale = "ja"

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
            notes=(
                "Japanese uses multiplicative composition (二百, 三千).",
                "百, 十 omit leading 一. Ordinal uses 番目 suffix.",
            ),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        validate_request(request, self.capabilities())
        value = request.value
        if request.form is NumeralForm.DIGITS:
            text = self._render_digits(value)
        elif request.form is NumeralForm.ORDINAL:
            text = self._render_cardinal(require_int(value)) + "番目"
        elif request.form is NumeralForm.YEAR:
            text = self._year(require_int(value))
        else:
            text = self._render_cardinal(require_int(value))
        return NumeralResult(
            text, request.locale, request.form, request.style, request.morphology
        )

    def _year(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidValueError("year form requires a non-negative integer")
        return self._render_cardinal(value)

    def _render_cardinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > _MAX_CARDINAL:
            raise InvalidValueError(
                "Japanese cardinal supports integers from -999999999999 through 999999999999"
            )
        if value < 0:
            return "マイナス" + self._render_cardinal(-value)
        if value == 0:
            return "零"
        if value < 10:
            return _DIGITS[value]
        parts: list[str] = []
        for scale, name in _SCALES:
            if value >= scale:
                quotient, value = divmod(value, scale)
                if scale >= 1_0000:
                    parts.append(self._render_cardinal(quotient) + name)
                else:
                    # 千, 百, 十 omit leading 一
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


__all__ = ["JapaneseRenderer"]
