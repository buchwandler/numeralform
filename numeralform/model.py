"""Immutable semantic models used by numeralform."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import TypeAlias

from .errors import InvalidRequestError, InvalidValueError


class _ValueEnum(str, Enum):
    @classmethod
    def coerce(cls, value):
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except ValueError as exc:
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


@dataclass(frozen=True, slots=True)
class Morphology:
    gender: Gender | None = None
    case: Case | None = None
    animacy: Animacy | None = None
    grammatical_number: str | None = None
    noun_class: str | None = None

    def __post_init__(self) -> None:
        for field in ("gender", "case", "animacy"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(
                    self, field, globals()[field.capitalize()].coerce(value)
                )
        for field in ("grammatical_number", "noun_class"):
            value = getattr(self, field)
            if value is not None and (not isinstance(value, str) or not value):
                raise InvalidRequestError(f"{field} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class NumeralRequest:
    value: NumericValue | int
    locale: str
    form: NumeralForm = NumeralForm.CARDINAL
    syntax: Syntax = Syntax.STANDALONE
    morphology: Morphology = Morphology()
    style: str | None = None

    def __post_init__(self) -> None:
        value = coerce_value(self.value)
        object.__setattr__(self, "value", value)
        if not isinstance(self.locale, str) or not self.locale.strip():
            raise InvalidRequestError("locale must be a non-empty string")
        normalized_form = NumeralForm.coerce(self.form)
        if normalized_form is NumeralForm.CARDINAL and not isinstance(value, int):
            normalized_form = {
                DigitSequence: NumeralForm.DIGITS,
                DecimalNumber: NumeralForm.DECIMAL,
                FractionNumber: NumeralForm.FRACTION,
            }[type(value)]
        object.__setattr__(self, "form", normalized_form)
        object.__setattr__(self, "syntax", Syntax.coerce(self.syntax))
        if not isinstance(self.morphology, Morphology):
            raise InvalidRequestError("morphology must be a Morphology instance")
        if self.style is not None and (
            not isinstance(self.style, str) or not self.style
        ):
            raise InvalidRequestError("style must be a non-empty string")


@dataclass(frozen=True, slots=True)
class NumeralResult:
    text: str
    locale: str
    form: NumeralForm
    style: str | None
    morphology: Morphology
