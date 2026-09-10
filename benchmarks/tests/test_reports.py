from __future__ import annotations

from benchmarks.validation.report import Mismatch, group_mismatches


def test_report_groups_by_dimensions():
    mismatch = Mismatch(
        "case",
        "es",
        "map",
        "cardinal",
        {"gender": "masculine"},
        "21",
        "veintiuno",
        "veintiún",
    )
    groups = group_mismatches([mismatch])
    key = next(iter(groups))
    assert key[:4] == ("es", "map", "cardinal", (("gender", "masculine"),))
    assert "10^1" in key[4]
    assert key[5] == "lexical difference"


def test_exception_mismatch_keeps_exception_metadata():
    mismatch = Mismatch(
        "case",
        "zh",
        "external-num2words",
        "year",
        {},
        1000,
        "",
        "<exception UnsupportedLocaleError: unsupported>",
        "exception",
        expected_exception_type="NotImplementedError",
        actual_exception_type="UnsupportedLocaleError",
        actual_exception_message="unsupported",
    )
    assert mismatch.shape == "exception type difference"
    assert mismatch.value_range == "10^3..10^4"
