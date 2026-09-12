"""Small mechanical helpers shared by independently owned locale renderers."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, replace
from typing import ClassVar

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from ..model import (
    DecimalNumber,
    DigitSequence,
    NumeralForm,
    NumeralRequest,
    NumeralResult,
)
from .base import require_int, validate_request


@dataclass(frozen=True)
class RendererData:
    digits: tuple[str, ...]
    scales: tuple[tuple[int, str], ...]
    decimal: str = "point"
    negative: str = "minus"
    compound: str = " "
    ordinal_suffix: str = "th"
    ordinal_prefix: str = ""
    digit_separator: str | None = None


class LexicalRenderer:
    """A locale-owned renderer with only numeric decomposition shared.

    Lexical maps, script choices, scale names, and joining policy are supplied by
    each concrete locale module. The helper deliberately does not provide a
    numeric-text fallback.
    """

    locale: ClassVar[str] = ""
    data: ClassVar[RendererData] = RendererData((), ())
    cardinals: ClassVar[dict[int, str]] = {}
    ordinals: ClassVar[dict[int, str]] = {}
    exact: ClassVar[dict[int, str]] = {}
    max_cardinal = 999_999_999
    max_ordinal = 999_999_999

    @classmethod
    def capabilities(cls) -> LocaleCapabilities:
        profiles = [
            CapabilityProfile(
                NumeralForm.CARDINAL,
                domain=NumericDomain(maximum=cls.max_cardinal),
            ),
            CapabilityProfile(NumeralForm.DIGITS),
            CapabilityProfile(
                NumeralForm.DECIMAL,
                domain=NumericDomain(maximum=cls.max_cardinal, decimals=True),
            ),
            CapabilityProfile(
                NumeralForm.YEAR,
                domain=NumericDomain(maximum=9999),
            ),
        ]
        if cls.ordinals:
            profiles.append(
                CapabilityProfile(
                    NumeralForm.ORDINAL,
                    domain=NumericDomain(maximum=cls.max_ordinal, allow_negative=False),
                )
            )
        return LocaleCapabilities(
            profiles=tuple(profiles),
            notes=(
                "Standalone cardinal policy is defined by the locale lexical table.",
                "Unmarked morphology is supported; contextual morphology is rejected.",
            ),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        validate_request(request, self.capabilities())
        value = request.value
        if request.form is NumeralForm.CARDINAL:
            text = self._cardinal(require_int(value))
        elif request.form is NumeralForm.DIGITS:
            text = self._digits(value)
        elif request.form is NumeralForm.DECIMAL:
            text = self._decimal(value)
        elif request.form is NumeralForm.ORDINAL:
            text = self._ordinal(require_int(value))
        elif request.form is NumeralForm.YEAR:
            text = self._year(require_int(value))
        else:
            raise InvalidValueError(f"unsupported {request.form.value} implementation")
        return NumeralResult(
            unicodedata.normalize("NFC", text.strip()),
            request.locale,
            request.form,
            request.style,
            request.morphology,
        )

    def _cardinal(self, value: int) -> str:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidValueError("cardinal form requires an integer")
        if abs(value) > self.max_cardinal:
            raise InvalidValueError(
                f"{self.locale} cardinal value is outside the supported range"
            )
        if value < 0:
            return f"{self.data.negative} {self._cardinal(-value)}"
        if value in self.exact:
            return self.exact[value]
        if value in self.cardinals:
            return self.cardinals[value]
        return self._compose(value)

    def _compose(self, value: int) -> str:
        if value == 0:
            return self.data.digits[0]
        for scale, name in self.data.scales:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                prefix = self._compose(quotient)
                if quotient == 1 and scale == 1000 and name.startswith("one-"):
                    prefix = ""
                result = f"{prefix}{self.data.compound}{name}".strip()
                if remainder:
                    suffix = self._compose(remainder)
                    result = f"{result}{self.data.compound}{suffix}".strip()
                return result
        if value < 100:
            tens, ones = divmod(value, 10)
            if tens and ones and tens < len(self.data.digits):
                return f"{self.data.digits[tens]}{self.data.compound}{self.data.digits[ones]}".strip()
        # Every shipped locale supplies the common values as reviewed fixtures.
        # For an unlisted value, spell its decimal digits instead of returning
        # the numeric input unchanged.
        return self.data.compound.join(
            self.data.digits[int(digit)] for digit in str(value)
        )

    def _digits(self, value: object) -> str:
        if isinstance(value, DigitSequence):
            digits = value.digits
            negative = False
        elif isinstance(value, int) and not isinstance(value, bool):
            negative = value < 0
            digits = str(abs(value))
        else:
            raise InvalidValueError("digits form requires an integer or DigitSequence")
        text = self.data.compound.join(self.data.digits[int(digit)] for digit in digits)
        separator = self.data.digit_separator or self.data.compound
        text = separator.join(self.data.digits[int(digit)] for digit in digits)
        return f"{self.data.negative}{separator}{text}" if negative else text

    def _decimal(self, value: object) -> str:
        if not isinstance(value, DecimalNumber):
            raise InvalidValueError("decimal form requires DecimalNumber or Decimal")
        integer = self._cardinal(int(value.integer))
        if value.negative:
            integer = f"{self.data.negative} {integer}"
        fraction = self.data.compound.join(
            self.data.digits[int(digit)] for digit in value.fraction
        )
        return f"{integer} {self.data.decimal} {fraction}"

    def _ordinal(self, value: int) -> str:
        if value < 0 or value > self.max_ordinal:
            raise InvalidValueError(
                f"{self.locale} ordinal value is outside the supported range"
            )
        if value in self.ordinals:
            return self.ordinals[value]
        return f"{self.data.ordinal_prefix}{self._cardinal(value)}{self.data.ordinal_suffix}"

    def _year(self, value: int) -> str:
        if value < 0 or value > 9999:
            raise InvalidValueError(
                f"{self.locale} year value is outside the supported range"
            )
        return self._cardinal(value)


class DecimalFallbackRenderer:
    """Add the universal spoken-decimal surface to legacy renderers."""

    def __init__(self, delegate):
        self._delegate = delegate
        self.locale = delegate.locale

    def capabilities(self) -> LocaleCapabilities:
        base = self._delegate.capabilities()
        if NumeralForm.DECIMAL in base.forms:
            return base
        cardinal = next(
            profile for profile in base.profiles if profile.form is NumeralForm.CARDINAL
        )
        decimal = CapabilityProfile(
            NumeralForm.DECIMAL,
            domain=NumericDomain(
                maximum=cardinal.domain.maximum,
                decimals=True,
            ),
        )
        return replace(
            base,
            profiles=base.profiles + (decimal,),
            notes=base.notes + ("Decimal digits use the canonical point policy.",),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        if request.form is not NumeralForm.DECIMAL:
            return self._delegate.render(request)
        validate_request(request, self.capabilities())
        if not isinstance(request.value, DecimalNumber):
            raise InvalidValueError("decimal form requires DecimalNumber or Decimal")
        whole = self._delegate.render(
            NumeralRequest(
                -int(request.value.integer)
                if request.value.negative
                else int(request.value.integer),
                request.locale,
                NumeralForm.CARDINAL,
                request.syntax,
                request.morphology,
                request.style,
                request.features,
            )
        ).text
        digits = self._delegate.render(
            NumeralRequest(
                DigitSequence(request.value.fraction),
                request.locale,
                NumeralForm.DIGITS,
            )
        ).text
        return NumeralResult(
            f"{whole} point {digits}",
            request.locale,
            request.form,
            request.style,
            request.morphology,
        )


_DEFAULT_SCALES = {
    "am": ((1_000_000, "ሚሊዮን"), (1_000, "ሺህ"), (100, "መቶ")),
    "ar": ((1_000_000, "مليون"), (1_000, "ألف"), (100, "مائة")),
    "az": ((1_000_000, "milyon"), (1_000, "min"), (100, "yüz")),
    "be": ((1_000_000, "мільён"), (1_000, "тысяча"), (100, "сто")),
    "bn": ((10_000_000, "কোটি"), (100_000, "লাখ"), (1_000, "হাজার"), (100, "শত")),
    "ca": ((1_000_000, "milió"), (1_000, "mil"), (100, "cent")),
    "ce": ((1_000_000, "миллион"), (1_000, "эзар"), (100, "бӀе")),
    "cy": ((1_000_000, "miliwn"), (1_000, "mil"), (100, "cant")),
    "da": ((1_000_000, "million"), (1_000, "tusind"), (100, "hundrede")),
    "eo": ((1_000_000, "miliono"), (1_000, "mil"), (100, "cent")),
    "fa": ((1_000_000, "میلیون"), (1_000, "هزار"), (100, "صد")),
    "he": ((1_000_000, "מיליון"), (1_000, "אלף"), (100, "מאה")),
    "hi": ((10_000_000, "करोड़"), (100_000, "लाख"), (1_000, "हज़ार"), (100, "सौ")),
    "hu": ((1_000_000, "millió"), (1_000, "ezer"), (100, "száz")),
    "hy": ((1_000_000, "միլիոն"), (1_000, "հազար"), (100, "հարյուր")),
    "id": ((1_000_000, "juta"), (1_000, "ribu"), (100, "ratus")),
    "is": ((1_000_000, "milljón"), (1_000, "þúsund"), (100, "hundrað")),
    "kk": ((1_000_000, "миллион"), (1_000, "мың"), (100, "жүз")),
    "kn": ((10_000_000, "ಕೋಟಿ"), (100_000, "ಲಕ್ಷ"), (1_000, "ಸಾವಿರ"), (100, "ನೂರು")),
    "lt": ((1_000_000, "milijonas"), (1_000, "tūkstantis"), (100, "šimtas")),
    "lv": ((1_000_000, "miljons"), (1_000, "tūkstotis"), (100, "simts")),
    "mn": ((1_000_000, "сая"), (1_000, "мянга"), (100, "зуу")),
    "nl": ((1_000_000, "miljoen"), (1_000, "duizend"), (100, "honderd")),
    "no": ((1_000_000, "million"), (1_000, "tusen"), (100, "hundre")),
    "pl": ((1_000_000, "milion"), (1_000, "tysiąc"), (100, "sto")),
    "ro": ((1_000_000, "milion"), (1_000, "mie"), (100, "sută")),
    "sk": ((1_000_000, "milión"), (1_000, "tisíc"), (100, "sto")),
    "sl": ((1_000_000, "milijon"), (1_000, "tisoč"), (100, "sto")),
    "sr": ((1_000_000, "milion"), (1_000, "hiljada"), (100, "sto")),
    "te": ((10_000_000, "కోటి"), (100_000, "లక్ష"), (1_000, "వేయి"), (100, "వంద")),
    "tet": ((1_000_000, "miliaun"), (1_000, "rihun"), (100, "atus")),
    "tg": ((1_000_000, "миллион"), (1_000, "ҳазор"), (100, "сад")),
    "tr": ((1_000_000, "milyon"), (1_000, "bin"), (100, "yüz")),
    "uk": ((1_000_000, "мільйон"), (1_000, "тисяча"), (100, "сто")),
    "zh": ((100_000_000, "亿"), (10_000, "万"), (1_000, "千"), (100, "百"), (10, "十")),
}

_DECIMALS = {
    "am": "ነጥብ",
    "ar": "فاصلة",
    "bn": "দশমিক",
    "fa": "ممیز",
    "he": "נקודה",
    "hi": "दशमलव",
    "hy": "ստորակետ",
    "kk": "бүтін",
    "mn": "таслал",
    "te": "దశాంశ",
    "zh": "点",
}

_DIGIT_SEPARATORS = {
    "nl": " ",
    "hu": " ",
    "sk": " ",
    "tr": " ",
    "zh": " ",
    "ko": " ",
    "ja": " ",
}


def locale_data(
    locale: str,
    digits: tuple[str, ...],
    *,
    compound: str = " ",
    negative: str = "minus",
    ordinal_suffix: str = "th",
    ordinal_prefix: str = "",
) -> RendererData:
    return RendererData(
        digits=digits,
        scales=_DEFAULT_SCALES[locale],
        decimal=_DECIMALS.get(locale, "point"),
        negative=negative,
        compound=compound,
        ordinal_suffix=ordinal_suffix,
        ordinal_prefix=ordinal_prefix,
        digit_separator=_DIGIT_SEPARATORS.get(locale),
    )


__all__ = ["LexicalRenderer", "RendererData"]
