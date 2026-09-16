"""Small mechanical helpers shared by independently owned locale renderers."""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
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
    digit_separator: str | None = None
    scale_forms: Mapping[int, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class DecimalPolicy:
    marker: str
    before_marker: str = " "
    after_marker: str = " "
    digit_separator: str = " "
    negative_prefix: str = "minus"
    negative_separator: str = " "


def contiguous_integer_domain(values: Mapping[int, str]) -> tuple[int, int] | None:
    """Return the largest contiguous integer block starting at the minimum key."""
    if not values:
        return None
    minimum = min(values)
    maximum = minimum
    while maximum + 1 in values:
        maximum += 1
    return minimum, maximum


# Per-class cache for the fixture-derived ordinal domain so hot render
# paths do not rescan the fixture table on every request.
_ORDINAL_DOMAINS: dict[type, NumericDomain | None] = {}


class LexicalRenderer:
    """A locale-owned renderer with only numeric decomposition shared.

    Lexical maps, script choices, scale names, and joining policy are supplied by
    each concrete locale module. The helper deliberately does not provide a
    numeric-text fallback and deliberately does not synthesize word ordinals:
    ordinal surfaces come either from reviewed fixtures or from a locale-owned
    ``_ordinal()`` override.
    """

    locale: ClassVar[str] = ""
    data: ClassVar[RendererData] = RendererData((), ())
    cardinals: ClassVar[dict[int, str]] = {}
    ordinals: ClassVar[dict[int, str]] = {}
    exact: ClassVar[dict[int, str]] = {}
    max_cardinal = 999_999_999

    @classmethod
    def _ordinal_domain(cls) -> NumericDomain | None:
        """The reviewed continuous word-ordinal domain, or None if unreviewed."""
        try:
            return _ORDINAL_DOMAINS[cls]
        except KeyError:
            block = contiguous_integer_domain(cls.ordinals)
            domain = (
                NumericDomain(minimum=block[0], maximum=block[1], allow_negative=False)
                if block
                else None
            )
            _ORDINAL_DOMAINS[cls] = domain
            return domain

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
        ordinal_domain = cls._ordinal_domain()
        if ordinal_domain is not None:
            profiles.append(
                CapabilityProfile(NumeralForm.ORDINAL, domain=ordinal_domain)
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

    def _scale_prefix(self, scale: int, quotient: int) -> str:
        if quotient == 1 and scale == 1000:
            return ""
        return self._compose(quotient)

    def _scale_name(self, scale: int, quotient: int) -> str:
        base = dict(self.data.scales)[scale]
        forms = self.data.scale_forms.get(scale)
        if not forms:
            return base.removeprefix("one-")
        if len(forms) == 2:
            return forms[0] if quotient == 1 else forms[1]
        if quotient == 1:
            return forms[0]
        if quotient % 100 in (11, 12, 13, 14):
            return forms[2]
        if quotient % 10 in (2, 3, 4):
            return forms[1]
        return forms[2]

    def _join_scale(
        self,
        *,
        scale: int,
        quotient: int,
        prefix: str,
        scale_name: str,
        remainder: int,
        suffix: str,
    ) -> str:
        result = f"{prefix}{self.data.compound}{scale_name}".strip()
        if remainder:
            result = f"{result}{self.data.compound}{suffix}".strip()
        return result

    def _compose(self, value: int) -> str:
        if value in self.exact:
            return self.exact[value]
        if value in self.cardinals:
            return self.cardinals[value]
        if value == 0:
            return self.data.digits[0]
        for scale, _name in self.data.scales:
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                prefix = self._scale_prefix(scale, quotient)
                scale_name = self._scale_name(scale, quotient)
                suffix = self._compose(remainder) if remainder else ""
                return self._join_scale(
                    scale=scale,
                    quotient=quotient,
                    prefix=prefix,
                    scale_name=scale_name,
                    remainder=remainder,
                    suffix=suffix,
                )
        if value < 100:
            tens, ones = divmod(value, 10)
            if tens and ones and tens < len(self.data.digits):
                return f"{self.data.digits[tens]}{self.data.compound}{self.data.digits[ones]}".strip()
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
        policy = decimal_policy(self.locale)
        integer = self._cardinal(int(value.integer))
        if value.negative:
            integer = (
                f"{policy.negative_prefix}{policy.negative_separator}{integer}".strip()
            )
        fraction = policy.digit_separator.join(
            self.data.digits[int(digit)] for digit in value.fraction
        )
        return (
            f"{integer}{policy.before_marker}{policy.marker}"
            f"{policy.after_marker}{fraction}"
        )

    def _ordinal(self, value: int) -> str:
        domain = self._ordinal_domain()
        if domain is None or value < (domain.minimum or 0) or value > domain.maximum:
            raise InvalidValueError(
                f"{self.locale} ordinal value is outside the supported range"
            )
        try:
            return self.ordinals[value]
        except KeyError as exc:
            raise InvalidValueError(
                f"{self.locale} ordinal value {value} has no reviewed rendering"
            ) from exc

    def _year(self, value: int) -> str:
        if value < 0 or value > 9999:
            raise InvalidValueError(
                f"{self.locale} year value is outside the supported range"
            )
        text = self._cardinal(value)
        suffix = _YEAR_SUFFIXES.get(self.locale, "")
        return f"{text}{suffix}"


_YEAR_SUFFIXES = {
    "am": "",
    "ar": "",
    "az": "",
    "be": "",
    "bn": " সাল",
    "ca": "",
    "ce": "",
    "cy": "",
    "da": "",
    "eo": "",
    "fa": "",
    "he": "",
    "hi": "",
    "hy": " թվական",
    "id": "",
    "is": "",
    "lt": "",
    "lv": "",
    "mn": " он",
    "nl": "",
    "no": "",
    "pl": "",
    "ro": "",
    "sk": "",
    "sl": "",
    "sr": "",
    "te": "",
    "tet": "",
    "tg": "",
    "tr": "",
    "uk": "",
}


_DECIMAL_POLICIES: dict[str, DecimalPolicy] = {
    "am": DecimalPolicy("ነጥብ"),
    "ar": DecimalPolicy("فاصلة", negative_prefix="سالب"),
    "az": DecimalPolicy("nöqtə", negative_prefix="mənfi"),
    "be": DecimalPolicy("коска", negative_prefix="мінус"),
    "bn": DecimalPolicy("দশমিক", negative_prefix="ঋণাত্মক"),
    "ca": DecimalPolicy("punt", negative_prefix="menys"),
    "da": DecimalPolicy("komma", negative_prefix="minus"),
    "de": DecimalPolicy("Komma", negative_prefix="minus"),
    "eo": DecimalPolicy("komo", negative_prefix="minus"),
    "fa": DecimalPolicy("ممیز", negative_prefix="منفی"),
    "fi": DecimalPolicy("pilkku", negative_prefix="miinus"),
    "fr": DecimalPolicy("virgule", negative_prefix="moins"),
    "he": DecimalPolicy("נקודה", negative_prefix="מינוס"),
    "hi": DecimalPolicy("दशमलव", negative_prefix="ऋणात्मक"),
    "hy": DecimalPolicy("ստորակետ", negative_prefix="մինուս"),
    "id": DecimalPolicy("koma", negative_prefix="minus"),
    "is": DecimalPolicy("komma", negative_prefix="mínus"),
    "it": DecimalPolicy("virgola", negative_prefix="meno"),
    "ja": DecimalPolicy(
        "点",
        before_marker="",
        after_marker="",
        digit_separator="",
        negative_prefix="マイナス",
        negative_separator="",
    ),
    "kn": DecimalPolicy("ದಶಮಾಂಶ", negative_prefix="ಮೈನಸ್"),
    "lt": DecimalPolicy("kablelis", negative_prefix="minus"),
    "lv": DecimalPolicy("komats", negative_prefix="mīnuss"),
    "mn": DecimalPolicy("таслал", negative_prefix="хасах"),
    "nl": DecimalPolicy("komma", negative_prefix="min"),
    "no": DecimalPolicy("komma", negative_prefix="minus"),
    "pl": DecimalPolicy("przecinek", negative_prefix="minus"),
    "pt": DecimalPolicy("vírgula", negative_prefix="menos"),
    "ro": DecimalPolicy("virgulă", negative_prefix="minus"),
    "sk": DecimalPolicy("čiarka", negative_prefix="mínus"),
    "sl": DecimalPolicy("celih", negative_prefix="minus"),
    "sr": DecimalPolicy("zapeta", negative_prefix="minus"),
    "sv": DecimalPolicy("komma", negative_prefix="minus"),
    "te": DecimalPolicy("దశాంశ", negative_prefix="మైనస్"),
    "tet": DecimalPolicy("vírgula", negative_prefix="minus"),
    "tg": DecimalPolicy("нуқта", negative_prefix="манфӣ"),
    "th": DecimalPolicy(
        "จุด",
        before_marker="",
        after_marker="",
        digit_separator="",
        negative_prefix="ติดลบ",
        negative_separator="",
    ),
    "tr": DecimalPolicy("virgül", negative_prefix="eksi"),
    "uk": DecimalPolicy("кома", negative_prefix="мінус"),
    "vi": DecimalPolicy("phẩy", negative_prefix="âm"),
    "zh": DecimalPolicy(
        "点",
        before_marker="",
        after_marker="",
        digit_separator="",
        negative_prefix="负",
        negative_separator="",
    ),
}


def decimal_policy(locale: str) -> DecimalPolicy:
    return _DECIMAL_POLICIES.get(
        locale, _DECIMAL_POLICIES.get(locale.split("-", 1)[0], DecimalPolicy("point"))
    )


def _decimal_word(locale: str) -> str:
    """Return the reviewed spoken decimal separator for a locale tag."""
    return decimal_policy(locale).marker


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
            notes=base.notes
            + ("Decimal digits use the reviewed locale separator policy.",),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        if request.form is not NumeralForm.DECIMAL:
            return self._delegate.render(request)
        validate_request(request, self.capabilities())
        if not isinstance(request.value, DecimalNumber):
            raise InvalidValueError("decimal form requires DecimalNumber or Decimal")
        policy = decimal_policy(request.locale)
        whole = self._delegate.render(
            NumeralRequest(
                int(request.value.integer),
                request.locale,
                NumeralForm.CARDINAL,
                request.syntax,
                request.morphology,
                request.style,
                request.features,
            )
        ).text
        if request.value.negative:
            whole = (
                f"{policy.negative_prefix}{policy.negative_separator}{whole}".strip()
            )
        digits = self._delegate.render(
            NumeralRequest(
                DigitSequence(request.value.fraction),
                request.locale,
                NumeralForm.DIGITS,
                request.syntax,
                request.morphology,
                request.style,
                request.features,
            )
        ).text
        if policy.digit_separator == "":
            digits = "".join(digits.split())
        return NumeralResult(
            f"{whole}{policy.before_marker}{policy.marker}"
            f"{policy.after_marker}{digits}",
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

_SCALE_FORMS: dict[str, dict[int, tuple[str, ...]]] = {
    "be": {
        1_000_000: ("мільён", "мільёны", "мільёнаў"),
        1_000: ("тысяча", "тысячы", "тысяч"),
    },
    "ca": {1_000_000: ("milió", "milions")},
    "da": {1_000_000: ("million", "millioner")},
    "eo": {1_000_000: ("miliono", "milionoj")},
    "he": {1_000_000: ("מיליון", "מיליונים"), 1_000: ("אלף", "אלפים")},
    "is": {1_000_000: ("milljón", "milljónir")},
    "lt": {
        1_000_000: ("milijonas", "milijonai", "milijonų"),
        1_000: ("tūkstantis", "tūkstančiai", "tūkstančių"),
    },
    "lv": {
        1_000_000: ("miljons", "miljoni", "miljonu"),
        1_000: ("tūkstotis", "tūkstoši", "tūkstošu"),
    },
    "nl": {1_000_000: ("miljoen", "miljoen")},
    "no": {1_000_000: ("million", "millioner")},
    "pl": {
        1_000_000: ("milion", "miliony", "milionów"),
        1_000: ("tysiąc", "tysiące", "tysięcy"),
    },
    "ro": {
        1_000_000: ("milion", "milioane"),
        1_000: ("mie", "mii"),
        100: ("sută", "sute"),
    },
    "sk": {
        1_000_000: ("milión", "milióny", "miliónov"),
        1_000: ("tisíc", "tisíce", "tisíc"),
    },
    "sl": {
        1_000_000: ("milijon", "milijoni", "milijonov"),
        1_000: ("tisoč", "tisoči", "tisoč"),
    },
    "sr": {
        1_000_000: ("milion", "miliona", "miliona"),
        1_000: ("hiljada", "hiljade", "hiljada"),
    },
    "uk": {
        1_000_000: ("мільйон", "мільйони", "мільйонів"),
        1_000: ("тисяча", "тисячі", "тисяч"),
    },
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
) -> RendererData:
    return RendererData(
        digits=digits,
        scales=_DEFAULT_SCALES[locale],
        decimal=decimal_policy(locale).marker,
        negative=negative,
        compound=compound,
        digit_separator=_DIGIT_SEPARATORS.get(locale),
        scale_forms=_SCALE_FORMS.get(locale, {}),
    )


__all__ = ["LexicalRenderer", "RendererData"]
