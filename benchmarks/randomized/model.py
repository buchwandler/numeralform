"""Immutable semantic cases and replayable execution results."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from numeralform import DecimalNumber

CASE_KINDS = ("cardinal", "decimal", "ordinal", "year", "currency")
EXECUTION_OUTCOMES = ("text", "exception")
DIFFERENTIAL_STATUSES = (
    "match",
    "variant",
    "mismatch",
    "oracle-error",
    "numeralform-error",
    "both-error",
)


@dataclass(frozen=True, slots=True)
class SerializedRandomValue:
    """A JSON-safe numeric value that preserves decimal spelling."""

    kind: str
    value: str

    def __post_init__(self) -> None:
        if self.kind not in {"int", "decimal"}:
            raise ValueError(f"unknown serialized value kind: {self.kind!r}")
        if not isinstance(self.value, str) or not self.value:
            raise ValueError("serialized value must be a non-empty string")
        if self.kind == "int":
            try:
                parsed = int(self.value)
            except ValueError as exc:
                raise ValueError(f"invalid integer value: {self.value!r}") from exc
            if str(parsed) != self.value and self.value not in {"-0"}:
                raise ValueError(f"integer value is not canonical: {self.value!r}")
        else:
            try:
                parsed = Decimal(self.value)
            except Exception as exc:
                raise ValueError(f"invalid decimal value: {self.value!r}") from exc
            if not parsed.is_finite() or "." not in self.value:
                raise ValueError(
                    f"decimal value must be finite and explicit: {self.value!r}"
                )

    @classmethod
    def from_python(cls, value: int | Decimal) -> SerializedRandomValue:
        if isinstance(value, bool):
            raise TypeError("boolean is not a random numeric value")
        if isinstance(value, int):
            return cls("int", str(value))
        if isinstance(value, Decimal):
            if not value.is_finite():
                raise ValueError("decimal value must be finite")
            text = format(value, "f")
            if "." not in text:
                text += ".0"
            return cls("decimal", text)
        raise TypeError(f"unsupported random value: {type(value).__name__}")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SerializedRandomValue:
        return cls(str(payload["kind"]), str(payload["value"]))

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "value": self.value}

    def python_value(self) -> int | Decimal:
        return int(self.value) if self.kind == "int" else Decimal(self.value)

    def decimal_number(self) -> DecimalNumber:
        if self.kind != "decimal":
            raise TypeError("DecimalNumber requires a decimal serialized value")
        text = self.value
        negative = text.startswith("-")
        text = text.lstrip("+-")
        integer, fraction = text.split(".", 1)
        return DecimalNumber(integer, fraction, negative)


@dataclass(frozen=True, slots=True)
class RandomCase:
    schema_version: int
    generator_version: int
    seed: int
    index: int
    case_id: str
    locale: str
    kind: str
    surface: str
    value: SerializedRandomValue
    currency: str | None = None
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in CASE_KINDS:
            raise ValueError(f"unknown random case kind: {self.kind!r}")
        if self.index < 0:
            raise ValueError("case index must be non-negative")
        if not self.locale or not self.case_id or not isinstance(self.surface, str):
            raise ValueError("locale, case_id, and surface are required")
        if self.kind in {"decimal", "currency"} and self.value.kind != "decimal":
            raise ValueError(f"{self.kind} cases require decimal values")
        if self.kind not in {"decimal", "currency"} and self.value.kind != "int":
            raise ValueError(f"{self.kind} cases require integer values")
        if self.kind == "currency" and not self.currency:
            raise ValueError("currency cases require an ISO currency code")
        if self.kind != "currency" and self.currency is not None:
            raise ValueError("only currency cases may specify a currency")
        object.__setattr__(self, "tags", tuple(self.tags))

    def python_value(self) -> int | Decimal:
        return self.value.python_value()

    def as_decimal_number(self) -> DecimalNumber:
        return self.value.decimal_number()

    def decimal_number(self) -> DecimalNumber:
        return self.value.decimal_number()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generator_version": self.generator_version,
            "seed": self.seed,
            "index": self.index,
            "case_id": self.case_id,
            "locale": self.locale,
            "kind": self.kind,
            "surface": self.surface,
            "value": self.value.to_dict(),
            "currency": self.currency,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RandomCase:
        return cls(
            schema_version=int(payload["schema_version"]),
            generator_version=int(payload["generator_version"]),
            seed=int(payload["seed"]),
            index=int(payload["index"]),
            case_id=str(payload["case_id"]),
            locale=str(payload["locale"]),
            kind=str(payload["kind"]),
            surface=str(payload["surface"]),
            value=SerializedRandomValue.from_dict(payload["value"]),
            currency=payload.get("currency"),
            tags=tuple(payload.get("tags", ())),
        )


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    outcome: str
    text: str | None = None
    exception_type: str | None = None
    exception_message: str | None = None

    def __post_init__(self) -> None:
        if self.outcome not in EXECUTION_OUTCOMES:
            raise ValueError(f"unknown execution outcome: {self.outcome!r}")
        if self.outcome == "text" and self.text is None:
            raise ValueError("text outcomes require text")
        if self.outcome == "exception" and not self.exception_type:
            raise ValueError("exception outcomes require exception type")

    @classmethod
    def text_result(cls, text: str) -> ExecutionResult:
        return cls("text", text=text)

    @classmethod
    def exception_result(cls, exc: Exception) -> ExecutionResult:
        return cls(
            "exception",
            exception_type=type(exc).__name__,
            exception_message=str(exc),
        )

    def to_dict(self) -> dict[str, str | None]:
        return {
            "outcome": self.outcome,
            "text": self.text,
            "exception_type": self.exception_type,
            "exception_message": self.exception_message,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ExecutionResult:
        return cls(
            outcome=str(payload["outcome"]),
            text=payload.get("text"),
            exception_type=payload.get("exception_type"),
            exception_message=payload.get("exception_message"),
        )


@dataclass(frozen=True, slots=True)
class DifferentialResult:
    case: RandomCase
    status: str
    num2words: ExecutionResult
    numeralform: ExecutionResult
    difference_shape: str | None = None
    equivalence_rule: str | None = None

    def __post_init__(self) -> None:
        if self.status not in DIFFERENTIAL_STATUSES:
            raise ValueError(f"unknown differential status: {self.status!r}")
        if self.status == "match" and (
            self.difference_shape is not None or self.equivalence_rule is not None
        ):
            raise ValueError("matches cannot have difference metadata")
        if self.status == "variant" and not self.equivalence_rule:
            raise ValueError("variants require an equivalence rule")
        if self.status != "variant" and self.equivalence_rule is not None:
            raise ValueError("only variants may have an equivalence rule")

    def to_dict(self) -> dict[str, Any]:
        return {
            "case": self.case.to_dict(),
            "status": self.status,
            "difference_shape": self.difference_shape,
            "num2words": self.num2words.to_dict(),
            "equivalence_rule": self.equivalence_rule,
            "numeralform": self.numeralform.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DifferentialResult:
        return cls(
            case=RandomCase.from_dict(payload["case"]),
            status=str(payload["status"]),
            difference_shape=payload.get("difference_shape"),
            num2words=ExecutionResult.from_dict(payload["num2words"]),
            equivalence_rule=payload.get("equivalence_rule"),
            numeralform=ExecutionResult.from_dict(payload["numeralform"]),
        )


def json_dumps(value: Any) -> str:
    """Serialize benchmark payloads with stable UTF-8 JSON formatting."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "CASE_KINDS",
    "DIFFERENTIAL_STATUSES",
    "EXECUTION_OUTCOMES",
    "DifferentialResult",
    "ExecutionResult",
    "RandomCase",
    "SerializedRandomValue",
    "json_dumps",
]
