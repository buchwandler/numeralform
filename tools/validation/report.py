"""Human-readable mismatch diagnostics and grouped reports."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from .normalize import codepoint_repr


@dataclass(frozen=True, slots=True)
class Mismatch:
    case_id: str
    locale: str
    mapping: str | None
    form: str
    morphology: dict[str, str]
    value: Any
    expected: str
    actual: str
    expectation_kind: str = "text"
    expected_text: str | None = None
    actual_text: str | None = None
    expected_exception_type: str | None = None
    expected_exception_message_pattern: str | None = None
    actual_exception_type: str | None = None
    actual_exception_message: str | None = None

    def __post_init__(self) -> None:
        if self.expectation_kind not in {"text", "exception"}:
            raise ValueError(f"unknown expectation kind: {self.expectation_kind!r}")

    @property
    def _expected_text(self) -> str:
        return self.expected if self.expected_text is None else self.expected_text

    @property
    def _actual_text(self) -> str:
        return self.actual if self.actual_text is None else self.actual_text

    @property
    def shape(self) -> str:
        if self.expectation_kind == "exception":
            if self.actual_exception_type is None:
                return "expected exception but returned text"
            if self.expected_exception_type != self.actual_exception_type:
                return "exception type difference"
            if self.expected_exception_message_pattern is not None:
                return "exception message difference"
            return "exception message difference"
        if self.actual_exception_type is not None:
            return "expected text but raised exception"
        expected = self._expected_text
        actual = self._actual_text
        if expected.replace("-", " ") == actual.replace("-", " "):
            return "hyphenation only"
        if expected.split() == actual.split():
            return "whitespace only"
        if expected.casefold() == actual.casefold():
            return "diacritic/code-point difference"
        if expected.startswith(actual) or actual.startswith(expected):
            return "prefix/suffix difference"
        if (
            " y " in expected
            or " y " in actual
            or " and " in expected
            or " and " in actual
        ):
            return "conjunction difference"
        return "lexical difference"

    @property
    def value_range(self) -> str:
        numeric: Decimal | None = None
        if isinstance(self.value, bool):
            return "unknown"
        if isinstance(self.value, int):
            numeric = Decimal(self.value)
        elif isinstance(self.value, (float, Decimal)):
            try:
                numeric = Decimal(str(self.value))
            except InvalidOperation:
                numeric = None
        elif isinstance(self.value, str):
            try:
                numeric = Decimal(self.value)
            except InvalidOperation:
                numeric = None
        if numeric is None or not numeric.is_finite():
            return "unknown"
        if numeric == 0:
            magnitude = 1
        else:
            magnitude = numeric.copy_abs().adjusted() + 1
        return f"10^{magnitude - 1}..10^{magnitude}"


def group_mismatches(
    mismatches: list[Mismatch],
) -> dict[
    tuple[str, str | None, str, tuple[tuple[str, str], ...], str, str], list[Mismatch]
]:
    groups: dict[
        tuple[str, str | None, str, tuple[tuple[str, str], ...], str, str],
        list[Mismatch],
    ] = defaultdict(list)
    for mismatch in mismatches:
        key = (
            mismatch.locale,
            mismatch.mapping,
            mismatch.form,
            tuple(sorted(mismatch.morphology.items())),
            mismatch.value_range,
            mismatch.shape,
        )
        groups[key].append(mismatch)
    return dict(groups)


def format_mismatches(mismatches: list[Mismatch]) -> str:
    lines = ["VALIDATION MISMATCHES", ""]
    for item in mismatches:
        lines.extend(
            (
                f"case:      {item.case_id}",
                f"locale:    {item.locale}",
                f"mapping:   {item.mapping or '-'}",
                f"form:      {item.form}",
                f"morphology: {item.morphology}",
                f"value:     {item.value!r}",
                f"value range: {item.value_range}",
                f"expectation: {item.expectation_kind}",
                f"difference: {item.shape}",
            )
        )
        if item.expectation_kind == "exception":
            lines.extend(
                (
                    f"expected exception: {item.expected_exception_type or '<none>'}",
                    "expected message pattern: "
                    + (item.expected_exception_message_pattern or "<none>"),
                    f"actual exception: {item.actual_exception_type or '<none>'}",
                    f"actual message: {item.actual_exception_message or '<none>'}",
                )
            )
        else:
            lines.extend(
                (
                    f"expected:  {item._expected_text!r}",
                    f"actual:    {item._actual_text!r}",
                    f"expected code points: {codepoint_repr(item._expected_text)}",
                    f"actual code points:   {codepoint_repr(item._actual_text)}",
                )
            )
        lines.append("")
    return "\n".join(lines)


def summarize(
    mismatches: list[Mismatch],
    *,
    cases: int,
    matches: int,
    reviewed_only: int = 0,
    exceptions: int = 0,
    files: int = 0,
    release: str | None = None,
) -> str:
    shapes = Counter(item.shape for item in mismatches)
    lines = [
        f"cases checked: {cases}",
        f"matches: {matches}",
        f"mismatches: {len(mismatches)}",
        f"reviewed-only cases: {reviewed_only}",
        f"exceptions used: {exceptions}",
        f"files checked: {files}",
    ]
    if release:
        lines.append(f"oracle release encoded in corpus: {release}")
    if shapes:
        lines.append(
            "difference shapes: "
            + ", ".join(f"{key}={value}" for key, value in sorted(shapes.items()))
        )
        for label, values in (
            (
                "compatibility mismatches by locale",
                Counter(item.locale for item in mismatches),
            ),
            (
                "compatibility mismatches by form",
                Counter(item.form for item in mismatches),
            ),
            (
                "compatibility mismatches by expectation kind",
                Counter(item.expectation_kind for item in mismatches),
            ),
        ):
            lines.append(f"{label}:")
            lines.extend(f"  {key}: {value}" for key, value in sorted(values.items()))
        lines.append("groups:")
        for key, group in sorted(
            group_mismatches(mismatches).items(), key=lambda item: repr(item[0])
        ):
            locale, mapping, form, morphology, value_range, shape = key
            lines.append(
                f"  locale={locale} mapping={mapping or '-'} form={form} "
                f"morphology={dict(morphology)} range={value_range} "
                f"shape={shape}: {len(group)}"
            )
    return "\n".join(lines)
