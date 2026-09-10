import json

from benchmarks.randomized.model import (
    DifferentialResult,
    ExecutionResult,
    RandomCase,
    SerializedRandomValue,
)
from benchmarks.randomized.report import write_reports


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
            "requested_cases": 3,
            "num2words": {"commit": "pin"},
        },
        record_all=True,
    )
    summary = json.loads(paths["summary"].read_text())
    assert summary["counts"]["match"] == 1
    assert summary["counts"]["mismatch"] == 2
    assert summary["comparability"] == {
        "comparable_cases": 3,
        "exact_matches": 1,
        "exact_parity_rate": 1 / 3,
    }
    assert len(paths["differences"].read_text().splitlines()) == 2
    assert len(paths["all"].read_text().splitlines()) == 3
    payload = json.loads(paths["differences"].read_text().splitlines()[0])
    assert payload["case"]["case_id"] == case.case_id
    report = paths["report"].read_text()
    assert "grouped differences" in report
    assert "cases by locale" in report
    assert "comparable cases:" in report
    assert "count: 2" in report
