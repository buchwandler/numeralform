"""Safe serialized models for validation cases."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from numeralform import (
    DecimalNumber,
    DigitSequence,
    FractionNumber,
    Morphology,
    NumeralRequest,
)


@dataclass(frozen=True, slots=True)
class SerializedValue:
    kind: str
    value: str | None = None
    integer: str | None = None
    fraction: str | None = None
    negative: bool | None = None
    numerator: str | None = None
    denominator: str | None = None

    def to_json(self) -> dict[str, Any]:
        result: dict[str, Any] = {"kind": self.kind}
        for name in (
            "value",
            "integer",
            "fraction",
            "negative",
            "numerator",
            "denominator",
        ):
            value = getattr(self, name)
            if value is not None:
                result[name] = value
        return result

    @classmethod
    def from_python(cls, value: object) -> SerializedValue:
        if isinstance(value, bool):
            raise ValueError("boolean values are not valid validation values")  # noqa: TRY004
        if isinstance(value, int):
            return cls("int", value=str(value))
        if isinstance(value, DigitSequence):
            return cls("digits", value=value.digits)
        if isinstance(value, DecimalNumber):
            return cls(
                "decimal",
                integer=value.integer,
                fraction=value.fraction,
                negative=value.negative,
            )
        if isinstance(value, FractionNumber):
            return cls(
                "fraction",
                numerator=str(value.numerator),
                denominator=str(value.denominator),
            )
        raise ValueError(f"unsupported validation value: {type(value).__name__}")

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> SerializedValue:
        if not isinstance(data, dict) or not isinstance(data.get("kind"), str):
            raise ValueError("value must be an object with a string kind")  # noqa: TRY004
        value = cls(
            **{
                key: data[key]
                for key in (
                    "kind",
                    "value",
                    "integer",
                    "fraction",
                    "negative",
                    "numerator",
                    "denominator",
                )
                if key in data
            }
        )
        value.as_python()
        return value

    def as_python(self) -> object:
        if self.kind == "int":
            if self.value is None or not self.value.lstrip("-").isdigit():
                raise ValueError("int value must be a decimal string")
            return int(self.value)
        if self.kind == "digits":
            return DigitSequence(self.value or "")
        if self.kind == "decimal":
            return DecimalNumber(
                self.integer or "", self.fraction or "", bool(self.negative)
            )
        if self.kind == "fraction":
            if self.numerator is None or self.denominator is None:
                raise ValueError("fraction requires numerator and denominator")
            return FractionNumber(int(self.numerator), int(self.denominator))
        raise ValueError(f"unknown serialized value kind: {self.kind!r}")


@dataclass(frozen=True, slots=True)
class ValidationRequest:
    value: SerializedValue
    locale: str
    form: str
    syntax: str
    style: str | None = None
    morphology: dict[str, str] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "value": self.value.to_json(),
            "locale": self.locale,
            "form": self.form,
            "syntax": self.syntax,
            "style": self.style,
            "morphology": dict(self.morphology),
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ValidationRequest:
        if not isinstance(data, dict):
            raise ValueError("request must be an object")  # noqa: TRY004
        required = ("value", "locale", "form", "syntax")
        if any(key not in data for key in required):
            raise ValueError("request is missing required fields")
        morphology = data.get("morphology", {})
        if not isinstance(morphology, dict) or any(
            not isinstance(k, str) or not isinstance(v, str)
            for k, v in morphology.items()
        ):
            raise ValueError("morphology must be a string dictionary")
        return cls(
            SerializedValue.from_json(data["value"]),
            data["locale"],
            data["form"],
            data["syntax"],
            data.get("style"),
            morphology,
        )

    def as_numeral_request(self) -> NumeralRequest:
        return NumeralRequest(
            self.value.as_python(),
            self.locale,
            self.form,
            self.syntax,
            Morphology(**self.morphology),
            self.style,
        )


@dataclass(frozen=True, slots=True)
class ValidationCase:
    id: str
    request: ValidationRequest
    expected: str
    mapping: str | None = None
    oracle: dict[str, str] | None = None
    source: str | None = None
    note: str | None = None

    def to_json(self) -> dict[str, Any]:
        result: dict[str, Any] = {"id": self.id}
        if self.mapping is not None:
            result["mapping"] = self.mapping
        result["request"] = self.request.to_json()
        if self.oracle is not None:
            result["oracle"] = dict(self.oracle)
        result["expected"] = self.expected
        if self.source is not None:
            result["source"] = self.source
        if self.note is not None:
            result["note"] = self.note
        return result

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ValidationCase:
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("id"), str)
            or not isinstance(data.get("expected"), str)
        ):
            raise ValueError("case requires string id and expected")  # noqa: TRY004
        return cls(
            data["id"],
            ValidationRequest.from_json(data["request"]),
            data["expected"],
            data.get("mapping"),
            data.get("oracle"),
            data.get("source"),
            data.get("note"),
        )
