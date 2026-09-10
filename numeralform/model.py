"""Immutable semantic models used by numeralform."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from types import MappingProxyType
from typing import TypeAlias

from .errors import InvalidRequestError, InvalidValueError


class _ValueEnum(str, Enum):
    @classmethod
    def coerce(cls, value):
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except (TypeError, ValueError) as exc:
            choices = ", ".join(item.value for item in cls)
            raise InvalidRequestError(
                f"invalid {cls.__name__} {value!r}; expected one of {choices}"
            ) from exc


class Gender(_ValueEnum):
    MASCULINE = "masculine"
    FEMININE = "feminine"
    NEUTER = "neuter"
    COMMON = "common"


class Case(_ValueEnum):
    NOMINATIVE = "nominative"
    GENITIVE = "genitive"
    DATIVE = "dative"
    ACCUSATIVE = "accusative"
    INSTRUMENTAL = "instrumental"
    LOCATIVE = "locative"
    PREPOSITIONAL = "prepositional"
    VOCATIVE = "vocative"


class Animacy(_ValueEnum):
    ANIMATE = "animate"
    INANIMATE = "inanimate"


class Syntax(_ValueEnum):
    STANDALONE = "standalone"
    ATTRIBUTIVE = "attributive"
    SUBSTANTIVE = "substantive"
    ORDINAL_ADJECTIVAL = "ordinal-adjectival"
    COUNTER = "counter"


class NumeralForm(_ValueEnum):
    CARDINAL = "cardinal"
    ORDINAL = "ordinal"
    ORDINAL_NUMERIC = "ordinal_num"
    DIGITS = "digits"
    DECIMAL = "decimal"
    FRACTION = "fraction"
    YEAR = "year"


@dataclass(frozen=True, slots=True)
class DigitSequence:
    """A sequence of digits whose leading zeroes are semantically significant."""

    digits: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.digits, str)
            or not self.digits
            or not self.digits.isascii()
            or not self.digits.isdecimal()
        ):
            raise InvalidValueError("digits must be a non-empty ASCII digit string")


@dataclass(frozen=True, slots=True)
class DecimalNumber:
    """A decimal value retaining the visible fractional digits."""

    integer: str
    fraction: str
    negative: bool = False

    def __post_init__(self) -> None:
        if (
            not isinstance(self.integer, str)
            or not self.integer
            or not self.integer.isascii()
            or not self.integer.isdecimal()
        ):
            raise InvalidValueError("integer must be a non-empty ASCII digit string")
        if (
            not isinstance(self.fraction, str)
            or not self.fraction
            or not self.fraction.isascii()
            or not self.fraction.isdecimal()
        ):
            raise InvalidValueError("fraction must be a non-empty ASCII digit string")
        if not isinstance(self.negative, bool):
            raise InvalidValueError("negative must be a boolean")

    @classmethod
    def from_decimal(cls, value: Decimal) -> DecimalNumber:
        if not isinstance(value, Decimal) or not value.is_finite():
            raise InvalidValueError("value must be a finite Decimal")
        text = format(abs(value), "f")
        integer, fraction = text.split(".", 1) if "." in text else (text, "0")
        return cls(integer, fraction, value < 0)


@dataclass(frozen=True, slots=True)
class FractionNumber:
    """A rational value represented by an integer numerator and denominator."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if isinstance(self.numerator, bool) or not isinstance(self.numerator, int):
            raise InvalidValueError("numerator must be an integer")
        if (
            isinstance(self.denominator, bool)
            or not isinstance(self.denominator, int)
            or self.denominator <= 0
        ):
            raise InvalidValueError("denominator must be a positive integer")


NumericValue: TypeAlias = int | DigitSequence | DecimalNumber | FractionNumber
NumericInput: TypeAlias = NumericValue | Decimal | Fraction
FeatureScalar: TypeAlias = str | bool | tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LocaleFeatures:
    """Immutable escape hatch for locale-specific rendering features.

    Universal agreement belongs in :class:`Morphology`; orthographic and
    locale-specific switches belong here and are validated by capabilities.
    """

    values: Mapping[str, FeatureScalar] = field(default_factory=dict)

    def __post_init__(self) -> None:
        values = dict(self.values) if not isinstance(self.values, tuple) else {}
        for key, value in values.items():
            if not isinstance(key, str) or not key.strip():
                raise InvalidRequestError(
                    "locale feature names must be non-empty strings"
                )
            if not isinstance(value, (str, bool, tuple)):
                raise InvalidRequestError(
                    f"locale feature {key!r} must be a string, boolean, or tuple"
                )
            if isinstance(value, tuple) and not all(
                isinstance(item, str) for item in value
            ):
                raise InvalidRequestError(
                    f"locale feature {key!r} tuple values must be strings"
                )
        object.__setattr__(self, "values", MappingProxyType(values))

    def __getitem__(self, key: str) -> FeatureScalar:
        return self.values[key]

    def get(self, key: str, default=None):
        return self.values.get(key, default)

    def items(self):
        return self.values.items()


def coerce_value(value: object) -> NumericValue:
    if isinstance(value, bool):
        raise InvalidValueError("boolean values are not numeric values")
    if isinstance(value, (DigitSequence, DecimalNumber, FractionNumber)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        return DecimalNumber.from_decimal(value)
    if isinstance(value, Fraction):
        return FractionNumber(value.numerator, value.denominator)
    raise InvalidValueError(
        "value must be an int, DigitSequence, DecimalNumber, FractionNumber, Decimal, or Fraction"
    )


def _coerce_open_feature(enum_type, value, field: str):
    if isinstance(value, enum_type):
        return value
    if not isinstance(value, str) or not value.strip():
        raise InvalidRequestError(f"{field} must be a non-empty string")
    normalized = value.strip().lower()
    try:
        return enum_type(normalized)
    except ValueError:
        # Case, animacy, and future feature inventories are locale-extensible.
        return normalized


@dataclass(frozen=True, slots=True)
class Morphology:
    gender: Gender | str | None = None
    case: Case | str | None = None
    animacy: Animacy | str | None = None
    grammatical_number: str | None = None
    noun_class: str | None = None
    definiteness: str | None = None
    state: str | None = None

    def __post_init__(self) -> None:
        if self.gender is not None:
            object.__setattr__(self, "gender", Gender.coerce(self.gender))
        for field_name, enum_type in (("case", Case), ("animacy", Animacy)):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self, field_name, _coerce_open_feature(enum_type, value, field_name)
                )
        for field_name in (
            "grammatical_number",
            "noun_class",
            "definiteness",
            "state",
        ):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise InvalidRequestError(f"{field_name} must be a non-empty string")
            if isinstance(value, str):
                object.__setattr__(self, field_name, value.strip().lower())


@dataclass(frozen=True, slots=True)
class NumeralRequest:
    value: NumericValue | Decimal | Fraction
    locale: str
    form: NumeralForm = field(default=None)  # type: ignore[assignment]
    syntax: Syntax = Syntax.STANDALONE
    morphology: Morphology = Morphology()
    style: str | None = None
    features: LocaleFeatures = LocaleFeatures()

    def __post_init__(self) -> None:
        value = coerce_value(self.value)
        object.__setattr__(self, "value", value)
        if not isinstance(self.locale, str) or not self.locale.strip():
            raise InvalidRequestError("locale must be a non-empty string")
        normalized_form = (
            NumeralForm.coerce(self.form) if self.form is not None else None
        )
        if normalized_form is None:
            normalized_form = {
                int: NumeralForm.CARDINAL,
                DigitSequence: NumeralForm.DIGITS,
                DecimalNumber: NumeralForm.DECIMAL,
                FractionNumber: NumeralForm.FRACTION,
            }[type(value)]
        object.__setattr__(self, "form", normalized_form)
        object.__setattr__(self, "syntax", Syntax.coerce(self.syntax))
        if not isinstance(self.morphology, Morphology):
            raise InvalidRequestError("morphology must be a Morphology instance")
        if not isinstance(self.features, LocaleFeatures):
            object.__setattr__(self, "features", LocaleFeatures(self.features))
        if self.style is not None and (
            not isinstance(self.style, str) or not self.style.strip()
        ):
            raise InvalidRequestError("style must be a non-empty string")
        if isinstance(self.style, str):
            object.__setattr__(self, "style", self.style.strip())


@dataclass(frozen=True, slots=True)
class NumeralResult:
    text: str
    locale: str
    form: NumeralForm
    style: str | None
    morphology: Morphology
    requested_locale: str | None = None
    syntax: Syntax = Syntax.STANDALONE
    features: LocaleFeatures = LocaleFeatures()
