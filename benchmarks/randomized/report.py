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
    values = Counter(str(getattr(result.case, key)) for result in results)
    return dict(sorted(values.items()))


def _option_key(result: DifferentialResult) -> str:
    return json_dumps(dict(sorted(result.case.options.items())))


def _breakdown_options(results: Iterable[DifferentialResult]) -> dict[str, int]:
    values = Counter(_option_key(result) for result in results)
    return dict(sorted(values.items()))


def summarize(
    results: tuple[DifferentialResult, ...] | list[DifferentialResult],
    *,
    metadata: dict[str, Any],
    generation_stats: dict[str, int] | None = None,
) -> dict[str, Any]:
    counts = Counter(result.status for result in results)
    summary: dict[str, Any] = dict(metadata)
    summary.setdefault("schema_version", 2)
    summary.setdefault("generator_version", 2)
    summary["counts"] = {status: counts.get(status, 0) for status in DIFFERENTIAL_STATUSES}
    comparable_cases = counts.get("match", 0) + counts.get("variant", 0) + counts.get("mismatch", 0)
    semantic_matches = counts.get("match", 0) + counts.get("variant", 0)
    summary["comparability"] = {
        "comparable_cases": comparable_cases,
        "exact_matches": counts.get("match", 0),
        "accepted_variants": counts.get("variant", 0),
        "semantic_matches": semantic_matches,
        "exact_parity_rate": counts.get("match", 0) / comparable_cases if comparable_cases else 0.0,
        "semantic_parity_rate": semantic_matches / comparable_cases if comparable_cases else 0.0,
    }
    mismatches = (result for result in results if result.status == "mismatch")
    variants = (result for result in results if result.status == "variant")
    oracle_errors = (result for result in results if result.status == "oracle-error")
    summary["breakdowns"] = {
        "locale": _breakdown(results, "locale"),
        "oracle_locale": _breakdown(results, "oracle_locale"),
        "kind": _breakdown(results, "kind"),
        "currency": _breakdown((result for result in results if result.case.currency is not None), "currency"),
        "options": _breakdown_options(results),
        "options_by_status": dict(sorted(Counter(f"{_option_key(result)}|{result.status}" for result in results).items())),
        "transport": dict(sorted(Counter(result.case.transport for result in results).items())),
        "variant_id": dict(sorted(Counter(result.case.variant_id or "<default>" for result in results).items())),
        "difference_shape": dict(sorted(Counter(result.difference_shape for result in results if result.difference_shape).items())),
        "variants_by_locale": _breakdown(variants, "locale"),
        "variants_by_kind": _breakdown(variants, "kind"),
        "variants_by_rule": dict(sorted(Counter(result.equivalence_rule for result in results if result.status == "variant" and result.equivalence_rule).items())),
        "mismatches_by_locale": _breakdown(mismatches, "locale"),
        "mismatches_by_oracle_locale": _breakdown(mismatches, "oracle_locale"),
        "mismatches_by_kind": _breakdown(mismatches, "kind"),
        "oracle_errors_by_locale": _breakdown(oracle_errors, "locale"),
        "oracle_errors_by_kind": _breakdown((result for result in results if result.status == "oracle-error"), "kind"),
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
        result.case.oracle_locale,
        result.case.kind,
        result.case.currency,
        _option_key(result),
        result.case.variant_id,
        result.case.transport,
        result.case.call_variant,
        result.status,
        result.difference_shape,
        result.equivalence_rule,
    )


def _format_options(options: dict[str, Any]) -> str:
    if not options:
        return "{}"
    values = []
    for key, value in sorted(options.items()):
        if isinstance(value, bool):
            rendered = str(value).lower()
        elif isinstance(value, str):
            rendered = repr(value)
        else:
            rendered = str(value)
        values.append(f"{key}={rendered}")
    return "{" + ", ".join(values) + "}"


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
        "NUM2WORDS ↔ NUMERALFORM RANDOM DIFFERENTIAL BENCHMARK", "",
        f"target:             {metadata.get('target', 'canonical')}",
        f"seed:               {metadata.get('seed', '<unknown>')}",
        f"profile:            {metadata.get('profile', '<unknown>')}",
        f"generator version:  {metadata.get('generator_version', 2)}",
        f"cases:              {metadata.get('requested_cases', len(results))}",
        f"num2words commit:   {metadata.get('num2words', {}).get('commit', '<unknown>')}", "",
        f"matches:            {counts['match']}",
        f"mismatches:         {counts['mismatch']}",
        f"accepted variants:  {counts['variant']}",
        f"oracle errors:      {counts['oracle-error']}",
        f"numeralform errors: {counts['numeralform-error']}",
        f"both errors:        {counts['both-error']}",
        f"comparable cases:   {summary['comparability']['comparable_cases']}",
        f"exact parity:       {summary['comparability']['exact_parity_rate']:.2%}",
        f"semantic parity:    {summary['comparability']['semantic_parity_rate']:.2%}",
    ]
    locale_mapping = metadata.get("locale_mapping", {})
    if locale_mapping:
        lines.extend(("", "locale mapping:"))
        lines.extend(f"  num2words {oracle} -> numeralform {canonical}" for oracle, canonical in sorted(locale_mapping.items()))
    currency_minor_units = metadata.get("currency_minor_units", {})
    if currency_minor_units:
        lines.extend(("", "currency minor units:"))
        lines.extend(f"  {currency}: {digits}" for currency, digits in sorted(currency_minor_units.items()))
    for label, values in (
        ("cases by locale", summary["breakdowns"]["locale"]),
        ("cases by oracle locale", summary["breakdowns"]["oracle_locale"]),
        ("cases by kind", summary["breakdowns"]["kind"]),
        ("cases by option profile", summary["breakdowns"]["options"]),
        ("cases by transport", summary["breakdowns"]["transport"]),
        ("cases by variant profile", summary["breakdowns"]["variant_id"]),
        ("accepted variants by locale", summary["breakdowns"]["variants_by_locale"]),
        ("accepted variants by kind", summary["breakdowns"]["variants_by_kind"]),
        ("accepted variants by rule", summary["breakdowns"]["variants_by_rule"]),
        ("mismatches by locale", summary["breakdowns"]["mismatches_by_locale"]),
        ("mismatches by kind", summary["breakdowns"]["mismatches_by_kind"]),
        ("oracle errors by locale", summary["breakdowns"]["oracle_errors_by_locale"]),
        ("oracle errors by kind", summary["breakdowns"]["oracle_errors_by_kind"]),
        ("mismatches by difference shape", summary["breakdowns"]["difference_shape"]),
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
            lines.extend((
                f"  locale={first.case.locale} oracle_locale={first.case.oracle_locale} kind={first.case.kind} currency={first.case.currency or '-'} status={first.status} shape={first.difference_shape or first.status}",
                f"    options={_format_options(first.case.options)} transport={first.case.transport} variant={first.case.variant_id or '<default>'}",
                f"    count: {len(group)}", "    examples:",
            ))
            for example in group[:5]:
                lines.extend((
                    f"      case: {example.case.case_id}",
                    f"        surface: {example.case.surface!r}",
                    f"        semantic: {_result_value(example)}",
                    f"        num2words: {example.num2words.text if example.num2words.text is not None else '<exception: ' + str(example.num2words.exception_type) + '>'}",
                    f"        numeralform: {example.numeralform.text if example.numeralform.text is not None else '<exception: ' + str(example.numeralform.exception_type) + '>'}",
                ))
    differences = [result for result in results if result.status != "match"]
    if differences:
        lines.extend(("", f"sample differences (maximum {sample_limit})"))
        for result in differences[:sample_limit]:
            lines.extend((
                f"  case: {result.case.case_id}",
                f"    surface: {result.case.surface!r}",
                f"    status: {result.status}",
                f"    replay: python -m benchmarks.randomized --replay {output_path} --case-id {result.case.case_id}",
            ))
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
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    differences_path = output_dir / RESULT_FILENAMES["differences"]
    _write_jsonl(differences_path, (result.to_dict() for result in results if result.status != "match"))
    report_path = output_dir / RESULT_FILENAMES["report"]
    report_path.write_text(human_report(results, metadata=metadata, output_path=str(differences_path)), encoding="utf-8")
    paths = {"summary": summary_path, "differences": differences_path, "report": report_path}
    if record_all:
        all_path = output_dir / RESULT_FILENAMES["all"]
        _write_jsonl(all_path, (result.to_dict() for result in results))
        paths["all"] = all_path
    return paths


__all__ = ["human_report", "summarize", "write_reports"]
