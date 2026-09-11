from decimal import Decimal

from benchmarks.randomized.coverage import has_coverage_gap, summarize_coverage
from benchmarks.randomized.model import DifferentialResult, ExecutionResult, RandomCase, SerializedRandomValue


def result(kind, value, *, locale="en", transport="native", call_variant=None):
    case = RandomCase(
        3,
        3,
        1,
        0,
        f"case-{kind}-{value}",
        locale,
        kind,
        str(value),
        SerializedRandomValue.from_python(value),
        options={},
        transport=transport,
        call_variant=call_variant,
    )
    return DifferentialResult(case, "match", ExecutionResult.text_result("x"), ExecutionResult.text_result("x"))


def test_coverage_reports_dimensions_and_cell_statistics():
    results = (result("cardinal", 0), result("cardinal", 1, transport="string", call_variant="ordinal-bool"))
    coverage = summarize_coverage(results, {"transports": ["native", "string"], "call_variants": ["to", "ordinal-bool"]})
    assert coverage["transports_covered"] == ["native", "string"]
    assert coverage["call_variants_covered"] == ["ordinal-bool", "to"]
    assert coverage["min_cases_per_cell"] == 1
    assert coverage["max_cases_per_cell"] == 1
    assert not has_coverage_gap(coverage)


def test_coverage_reports_missing_required_dimension():
    coverage = summarize_coverage((result("decimal", Decimal("1.0")),), {"transports": ["native", "string"]})
    assert coverage["missing_cells"] == {"transports": ["string"]}
    assert has_coverage_gap(coverage)
