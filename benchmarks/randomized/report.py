"""Deterministic machine-readable and human-readable benchmark reports."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .model import DIFFERENTIAL_STATUSES, DifferentialResult, json_dumps

RESULT_FILENAMES = {
    "summary": "summary.json",
    "differences": "differences.jsonl",
    "report": "report.txt",
    "all": "all-results.jsonl",
}


def _breakdown(results: Iterable[DifferentialResult], key: str) -> dict[str, int]:
    values = Counter(getattr(result.case, key) for result in results)
    return dict(sorted(values.items()))


def summarize(
    results: tuple[DifferentialResult, ...] | list[DifferentialResult],
    *,
    metadata: dict[str, Any],
    generation_stats: dict[str, int] | None = None,
) -> dict[str, Any]:
    counts = Counter(result.status for result in results)
    summary: dict[str, Any] = dict(metadata)
    summary.setdefault("schema_version", 1)
    summary.setdefault("generator_version", 1)
    summary["generated_cases"] = len(results)
    summary["counts"] = {status: counts.get(status, 0) for status in DIFFERENTIAL_STATUSES}
    summary["breakdowns"] = {
        "locale": _breakdown(results, "locale"),
        "kind": _breakdown(results, "kind"),
        "currency": _breakdown(
            (result for result in results if result.case.currency is not None), "currency"
        ),
        "difference_shape": dict(
            sorted(Counter(result.difference_shape for result in results if result.difference_shape).items())
        ),
    }
    if generation_stats:
        summary["generation"] = dict(sorted(generation_stats.items()))
    return summary


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json_dumps(row) + "\n")


def _result_value(result: DifferentialResult) -> str:
    return result.case.value.kind + "(" + result.case.value.value + ")"


def _group_key(result: DifferentialResult) -> tuple[Any, ...]:
    return (
        result.case.locale,
        result.case.kind,
        result.case.currency,
        result.difference_shape,
        result.num2words.text,
        result.numeralform.text,
        result.num2words.exception_type,
        result.numeralform.exception_type,
    )


def human_report(
    results: tuple[DifferentialResult, ...] | list[DifferentialResult],
    *,
    metadata: dict[str, Any],
    output_path: str = "benchmarks/data/results/num2words-random/differences.jsonl",
    sample_limit: int = 20,
) -> str:
    summary = summarize(results, metadata=metadata)
    counts = summary["counts"]
    lines = [
        "NUM2WORDS ↔ NUMERALFORM RANDOM DIFFERENTIAL BENCHMARK",
        "",
        f"seed:               {metadata.get('seed', '<unknown>')}",
        f"generator version:  {metadata.get('generator_version', 1)}",
        f"profile:            {metadata.get('profile', '<unknown>')}",
        f"cases:              {metadata.get('requested_cases', len(results))}",
        f"generated cases:    {len(results)}",
        f"num2words commit:   {metadata.get('num2words', {}).get('commit', '<unknown>')}",
        "",
        f"matches:            {counts['match']}",
        f"mismatches:         {counts['mismatch']}",
        f"oracle errors:      {counts['oracle-error']}",
        f"numeralform errors: {counts['numeralform-error']}",
        f"both errors:        {counts['both-error']}",
    ]
    for label, values in (
        ("by locale", summary["breakdowns"]["locale"]),
        ("by kind", summary["breakdowns"]["kind"]),
        ("by difference shape", summary["breakdowns"]["difference_shape"]),
    ):
        lines.extend(("", label))
        lines.extend(f"  {key}: {value}" for key, value in values.items())
    groups: dict[tuple[Any, ...], list[DifferentialResult]] = defaultdict(list)
    for result in results:
        if result.status != "match":
            groups[_group_key(result)].append(result)
    if groups:
        lines.extend(("", "grouped differences"))
        for key, group in sorted(groups.items(), key=lambda item: repr(item[0])):
            first = group[0]
            lines.extend(
                (
                    f"  locale={first.case.locale} kind={first.case.kind} currency={first.case.currency or '-'} shape={first.difference_shape or first.status}",
                    f"    count: {len(group)}",
                    f"    first case: {first.case.case_id}",
                    f"    surface: {first.case.surface!r}",
                    f"    semantic: {_result_value(first)}",
                    f"    num2words: {first.num2words.text if first.num2words.text is not None else '<exception: ' + str(first.num2words.exception_type) + '>'}",
                    f"    numeralform: {first.numeralform.text if first.numeralform.text is not None else '<exception: ' + str(first.numeralform.exception_type) + '>'}",
                )
            )
    differences = [result for result in results if result.status != "match"]
    if differences:
        lines.extend(("", f"sample differences (maximum {sample_limit})"))
        for result in differences[:sample_limit]:
            lines.extend(
                (
                    f"  case: {result.case.case_id}",
                    f"    surface: {result.case.surface!r}",
                    f"    status: {result.status}",
                    f"    replay: python -m benchmarks.randomized --replay {output_path} --case-id {result.case.case_id}",
                )
            )
    return "\n".join(lines) + "\n"


def write_reports(
    results: tuple[DifferentialResult, ...] | list[DifferentialResult],
    output_dir: Path,
    *,
    metadata: dict[str, Any],
    generation_stats: dict[str, int] | None = None,
    record_all: bool = False,
) -> dict[str, Path]:
    """Write all deterministic report files and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    results = tuple(results)
    summary = summarize(results, metadata=metadata, generation_stats=generation_stats)
    summary_path = output_dir / RESULT_FILENAMES["summary"]
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    differences_path = output_dir / RESULT_FILENAMES["differences"]
    _write_jsonl(
        differences_path,
        (result.to_dict() for result in results if result.status != "match"),
    )
    report_path = output_dir / RESULT_FILENAMES["report"]
    report_path.write_text(
        human_report(
            results,
            metadata=metadata,
            output_path=str(differences_path),
        ),
        encoding="utf-8",
    )
    paths = {"summary": summary_path, "differences": differences_path, "report": report_path}
    if record_all:
        all_path = output_dir / RESULT_FILENAMES["all"]
        _write_jsonl(all_path, (result.to_dict() for result in results))
        paths["all"] = all_path
    return paths


__all__ = ["human_report", "summarize", "write_reports"]
