import json

from benchmarks.randomized.model import (
    DifferentialResult,
    ExecutionResult,
    RandomCase,
    SerializedRandomValue,
)
from benchmarks.randomized.report import summarize, write_reports


def test_report_outputs_are_replayable(tmp_path):
    case = RandomCase(
        1,
        1,
        42,
        0,
        "random-v1:42:000000",
        "en",
        "cardinal",
        "1",
        SerializedRandomValue.from_python(1),
    )
    results = [
        DifferentialResult(
            case,
            "match",
            ExecutionResult.text_result("one"),
            ExecutionResult.text_result("one"),
        ),
        DifferentialResult(
            case,
            "variant",
            ExecutionResult.text_result("twenty-one"),
            ExecutionResult.text_result("twenty one"),
            "hyphenation only",
            "surface:hyphenation only",
        ),
        DifferentialResult(
            case,
            "mismatch",
            ExecutionResult.text_result("one and"),
            ExecutionResult.text_result("one"),
            "conjunction difference",
        ),
        DifferentialResult(
            case,
            "mismatch",
            ExecutionResult.text_result("one and"),
            ExecutionResult.text_result("one"),
            "conjunction difference",
        ),
    ]
    paths = write_reports(
        results,
        tmp_path,
        metadata={
            "seed": 42,
            "profile": "shared",
            "target": "canonical",
            "requested_cases": 4,
            "num2words": {"commit": "pin"},
        },
        record_all=True,
    )
    summary = json.loads(paths["summary"].read_text())
    assert summary["schema_version"] == 2
    assert summary["counts"]["match"] == 1
    assert summary["counts"]["variant"] == 1
    assert summary["counts"]["mismatch"] == 2
    assert summary["comparability"] == {
        "comparable_cases": 4,
        "exact_matches": 1,
        "accepted_variants": 1,
        "semantic_matches": 2,
        "exact_parity_rate": 1 / 4,
        "semantic_parity_rate": 2 / 4,
    }
    assert summary["breakdowns"]["variants_by_rule"] == {"surface:hyphenation only": 1}
    assert len(paths["differences"].read_text().splitlines()) == 3
    assert len(paths["all"].read_text().splitlines()) == 4
    payload = json.loads(paths["differences"].read_text().splitlines()[0])
    assert payload["case"]["case_id"] == case.case_id
    assert payload["equivalence_rule"] == "surface:hyphenation only"
    report = paths["report"].read_text()
    assert "grouped differences" in report
    assert "cases by locale" in report
    assert "accepted variants:  1" in report
    assert "semantic parity:" in report
    assert "comparable cases:" in report
    assert "count: 2" in report


def test_report_breakdowns_materialize_status_subsets():
    def result(*, locale, oracle_locale, kind, status, shape):
        local_case = RandomCase(
            1,
            1,
            42,
            0,
            f"case-{locale}-{kind}-{status}",
            locale,
            kind,
            "1.0" if kind == "decimal" else "1",
            SerializedRandomValue("decimal", "1.0")
            if kind == "decimal"
            else SerializedRandomValue("int", "1"),
            oracle_locale=oracle_locale,
        )
        return DifferentialResult(
            local_case,
            status,
            ExecutionResult.text_result("oracle"),
            ExecutionResult.text_result("canonical"),
            shape,
            "variant:test" if status == "variant" else None,
        )

    results = [
        result(
            locale="en",
            oracle_locale="en-US",
            kind="decimal",
            status="variant",
            shape="lexical difference",
        ),
        result(
            locale="es",
            oracle_locale="es-ES",
            kind="year",
            status="variant",
            shape="whitespace only",
        ),
        result(
            locale="en",
            oracle_locale="en-US",
            kind="cardinal",
            status="mismatch",
            shape="conjunction difference",
        ),
        result(
            locale="fr",
            oracle_locale="fr-FR",
            kind="ordinal",
            status="mismatch",
            shape="lexical difference",
        ),
    ]
    summary = summarize(results, metadata={})
    breakdowns = summary["breakdowns"]
    assert breakdowns["variants_by_locale"] == {"en": 1, "es": 1}
    assert breakdowns["variants_by_kind"] == {"decimal": 1, "year": 1}
    assert breakdowns["mismatches_by_locale"] == {"en": 1, "fr": 1}
    assert breakdowns["mismatches_by_oracle_locale"] == {"en-US": 1, "fr-FR": 1}
    assert breakdowns["mismatches_by_kind"] == {"cardinal": 1, "ordinal": 1}
    assert breakdowns["differences_by_shape"] == {
        "conjunction difference": 1,
        "lexical difference": 2,
        "whitespace only": 1,
    }
    assert breakdowns["mismatches_by_shape"] == {
        "conjunction difference": 1,
        "lexical difference": 1,
    }
    assert breakdowns["variants_by_shape"] == {
        "lexical difference": 1,
        "whitespace only": 1,
    }
