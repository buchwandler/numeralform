"""Human-readable mismatch diagnostics and grouped reports."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from .normalize import codepoint_repr


@dataclass(frozen=True, slots=True)
class Mismatch:
    case_id: str
    locale: str
    mapping: str | None
    form: str
    morphology: dict[str, str]
    value: str
    expected: str
    actual: str

    @property
    def shape(self) -> str:
        if self.expected.replace("-", " ") == self.actual.replace("-", " "):
            return "hyphenation only"
        if self.expected.split() == self.actual.split():
            return "whitespace only"
        if self.expected.casefold() == self.actual.casefold():
            return "diacritic/code-point difference"
        if self.expected.startswith(self.actual) or self.actual.startswith(
            self.expected
        ):
            return "prefix/suffix difference"
        if (
            " y " in self.expected
            or " y " in self.actual
            or " and " in self.expected
            or " and " in self.actual
        ):
            return "conjunction difference"
        return "lexical difference"

    @property
    def value_range(self) -> str:
        digits = "".join(char for char in self.value if char.isdigit())
        magnitude = len(digits.lstrip("0")) or 1
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
                f"value:     {item.value}",
                f"value range: {item.value_range}",
                f"difference: {item.shape}",
                f"expected:  {item.expected!r}",
                f"actual:    {item.actual!r}",
                f"expected code points: {codepoint_repr(item.expected)}",
                f"actual code points:   {codepoint_repr(item.actual)}",
                "",
            )
        )
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
        lines.append("groups:")
        for key, group in sorted(
            group_mismatches(mismatches).items(), key=lambda item: repr(item[0])
        ):
            locale, mapping, form, morphology, value_range, shape = key
            lines.append(
                f"  locale={locale} mapping={mapping or '-'} form={form} morphology={dict(morphology)} range={value_range} shape={shape}: {len(group)}"
            )
    return "\n".join(lines)
