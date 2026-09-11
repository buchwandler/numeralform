"""Coverage accounting for randomized benchmark cases."""

from __future__ import annotations

from collections import Counter
from statistics import median
from typing import Iterable

from .model import DifferentialResult, RandomCase


def _boundary(case: RandomCase) -> str:
    value = abs(case.python_value())
    if value == 0:
        return "zero"
    if value == 1:
        return "one"
    if value < 100:
        return "small"
    if value < 1_000_000:
        return "medium"
    return "large"


def _values(cases: Iterable[RandomCase], key: str) -> list[str]:
    return sorted({str(getattr(case, key)) for case in cases})


def summarize_coverage(results: Iterable[DifferentialResult], expected: dict | None = None) -> dict:
    cases = [result.case for result in results]
    expected = expected or {}
    locale_kind = {f"{case.locale}|{case.kind}" for case in cases}
    option_profiles = {case.option_profile_id or "<default>" for case in cases}
    currency_cells = {f"{case.locale}|{case.currency}" for case in cases if case.currency}
    transports = {case.transport for case in cases}
    call_variants = {case.call_variant or "to" for case in cases}
    boundary_cells = {f"{case.kind}|{_boundary(case)}" for case in cases}

    dimensions = {
        "locales": _values(cases, "locale"),
        "kinds": _values(cases, "kind"),
        "locale_kind_cells": sorted(locale_kind),
        "option_profiles": sorted(option_profiles),
        "currency_cells": sorted(currency_cells),
        "transports": sorted(transports),
        "call_variants": sorted(call_variants),
        "numeric_boundaries": sorted(boundary_cells),
    }
    missing_cells = {
        name: sorted(set(values) - set(dimensions.get(name, ())))
        for name, values in expected.items()
        if name in dimensions
    }
    missing_cells = {name: values for name, values in missing_cells.items() if values}
    counts = Counter(
        f"{case.locale}|{case.kind}|{case.currency or '-'}|{case.option_profile_id or '<default>'}|"
        f"{case.transport}|{case.call_variant or 'to'}|{_boundary(case)}"
        for case in cases
    )
    cell_counts = list(counts.values())
    return {
        "locales_expected": len(expected.get("locales", dimensions["locales"])),
        "locales_covered": len(dimensions["locales"]),
        "locale_kind_cells_expected": len(expected.get("locale_kind_cells", dimensions["locale_kind_cells"])),
        "locale_kind_cells_covered": len(dimensions["locale_kind_cells"]),
        "option_profiles_expected": len(expected.get("option_profiles", dimensions["option_profiles"])),
        "option_profiles_covered": len(dimensions["option_profiles"]),
        "currency_cells_expected": len(expected.get("currency_cells", dimensions["currency_cells"])),
        "currency_cells_covered": len(dimensions["currency_cells"]),
        "transports_expected": expected.get("transports", dimensions["transports"]),
        "transports_covered": dimensions["transports"],
        "call_variants_expected": expected.get("call_variants", dimensions["call_variants"]),
        "call_variants_covered": dimensions["call_variants"],
        "numeric_boundaries_expected": expected.get("numeric_boundaries", dimensions["numeric_boundaries"]),
        "numeric_boundaries_covered": dimensions["numeric_boundaries"],
        "missing_cells": missing_cells,
        "min_cases_per_cell": min(cell_counts) if cell_counts else 0,
        "median_cases_per_cell": median(cell_counts) if cell_counts else 0,
        "max_cases_per_cell": max(cell_counts) if cell_counts else 0,
    }


def has_coverage_gap(coverage: dict) -> bool:
    return bool(coverage.get("missing_cells"))


__all__ = ["has_coverage_gap", "summarize_coverage"]
