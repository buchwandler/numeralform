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
class SerializedCompatValue:
    """Lossless JSON representation of a permissive legacy API value."""

    kind: str
    value: Any = None

    def to_json(self) -> dict[str, Any]:
        return {"kind": self.kind, "value": self.value}

    @classmethod
    def from_python(cls, value: object) -> SerializedCompatValue:
        from decimal import Decimal

        if isinstance(value, bool):
            return cls("bool", value)
        if isinstance(value, int):
            return cls("int", str(value))
        if isinstance(value, float):
            return cls("float", repr(value))
        if isinstance(value, Decimal):
            return cls("decimal", str(value))
        if isinstance(value, str):
            return cls("str", value)
        if isinstance(value, tuple):
            return cls("tuple", [cls.from_python(item).to_json() for item in value])
        raise ValueError(f"unsupported compatibility value: {type(value).__name__}")

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> SerializedCompatValue:
        if not isinstance(data, dict) or not isinstance(data.get("kind"), str):
            raise ValueError("compatibility value requires a string kind")  # noqa: TRY004
        value = cls(data["kind"], data.get("value"))
        value.as_python()
        return value

    def as_python(self) -> object:
        from decimal import Decimal

        if self.kind == "bool":
            if not isinstance(self.value, bool):
                raise ValueError("bool compatibility value must be boolean")
            return self.value
        if self.kind == "int":
            return int(str(self.value))
        if self.kind == "float":
            return float(str(self.value))
        if self.kind == "decimal":
            return Decimal(str(self.value))
        if self.kind == "str":
            if not isinstance(self.value, str):
                raise ValueError("str compatibility value must be a string")
            return self.value
        if self.kind == "tuple":
            if not isinstance(self.value, list):
                raise ValueError("tuple compatibility value must be a list")
            return tuple(
                SerializedCompatValue.from_json(item).as_python() for item in self.value
            )
        raise ValueError(f"unknown compatibility value kind: {self.kind!r}")


@dataclass(frozen=True, slots=True)
class CompatInvocation:
    """Serialized invocation of a legacy compatibility function."""

    function: str
    positional: tuple[SerializedCompatValue, ...] = ()
    kwargs: dict[str, SerializedCompatValue] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "function": self.function,
            "positional": [value.to_json() for value in self.positional],
            "kwargs": {
                key: value.to_json() for key, value in sorted(self.kwargs.items())
            },
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> CompatInvocation:
        if not isinstance(data, dict) or not isinstance(data.get("function"), str):
            raise ValueError("compatibility invocation requires a function")  # noqa: TRY004
        positional = tuple(
            SerializedCompatValue.from_json(item) for item in data.get("positional", [])
        )
        kwargs_data = data.get("kwargs", {})
        if not isinstance(kwargs_data, dict):
            raise ValueError("compatibility invocation kwargs must be an object")  # noqa: TRY004
        kwargs = {
            key: SerializedCompatValue.from_json(value)
            for key, value in kwargs_data.items()
        }
        return cls(data["function"], positional, kwargs)

    def as_python(self) -> tuple[str, list[object], dict[str, object]]:
        return (
            self.function,
            [value.as_python() for value in self.positional],
            {key: value.as_python() for key, value in self.kwargs.items()},
        )


@dataclass(frozen=True, slots=True)
class ValidationCase:
    id: str
    request: ValidationRequest | None
    expected: str
    mapping: str | None = None
    oracle: dict[str, str] | None = None
    source: str | None = None
    note: str | None = None
    target: str = "canonical"
    invocation: CompatInvocation | None = None
    expected_exception_type: str | None = None
    expected_exception_message_pattern: str | None = None

    def __post_init__(self) -> None:
        if self.request is None and self.invocation is None:
            raise ValueError("validation case requires request or invocation")
        if self.request is not None and self.invocation is not None:
            raise ValueError(
                "validation case cannot contain both request and invocation"
            )
        if self.target not in {"canonical", "compat:num2words-0.5.14"}:
            raise ValueError(f"unknown validation target: {self.target!r}")
        if self.expected_exception_type and self.target == "canonical":
            raise ValueError("canonical cases cannot declare compatibility exceptions")

    def to_json(self) -> dict[str, Any]:
        result: dict[str, Any] = {"id": self.id}
        if self.mapping is not None:
            result["mapping"] = self.mapping
        if self.request is not None:
            result["request"] = self.request.to_json()
        if self.invocation is not None:
            result["invocation"] = self.invocation.to_json()
        if self.target != "canonical":
            result["target"] = self.target
        if self.oracle is not None:
            result["oracle"] = dict(self.oracle)
        if self.expected_exception_type is None:
            result["expected"] = self.expected
        else:
            result["expectation"] = {
                "exception_type": self.expected_exception_type,
            }
            if self.expected_exception_message_pattern is not None:
                result["expectation"]["message_pattern"] = (
                    self.expected_exception_message_pattern
                )
        if self.source is not None:
            result["source"] = self.source
        if self.note is not None:
            result["note"] = self.note
        return result

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ValidationCase:
        if not isinstance(data, dict) or not isinstance(data.get("id"), str):
            raise ValueError("case requires a string id")  # noqa: TRY004
        request = (
            ValidationRequest.from_json(data["request"]) if "request" in data else None
        )
        invocation = (
            CompatInvocation.from_json(data["invocation"])
            if "invocation" in data
            else None
        )
        if request is None and invocation is None:
            raise ValueError("case requires request or invocation")
        expectation = data.get("expectation", {})
        if not isinstance(expectation, dict):
            raise ValueError("expectation must be an object")  # noqa: TRY004
        expected = data.get("expected", "")
        if not isinstance(expected, str):
            raise ValueError("expected must be a string")  # noqa: TRY004
        exception_type = expectation.get("exception_type")
        message_pattern = expectation.get("message_pattern")
        if exception_type is not None and not isinstance(exception_type, str):
            raise ValueError("expectation exception_type must be a string")
        if message_pattern is not None and not isinstance(message_pattern, str):
            raise ValueError("expectation message_pattern must be a string")
        target = data.get("target", "canonical")
        if not isinstance(target, str):
            raise ValueError("target must be a string")  # noqa: TRY004
        return cls(
            data["id"],
            request,
            expected,
            data.get("mapping"),
            data.get("oracle"),
            data.get("source"),
            data.get("note"),
            target,
            invocation,
            exception_type,
            message_pattern,
        )
