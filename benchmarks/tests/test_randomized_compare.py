from benchmarks.randomized.compare import compare_results, difference_shape
from benchmarks.randomized.model import (
    ExecutionResult,
    RandomCase,
    SerializedRandomValue,
)


def case():
    return RandomCase(1, 1, 1, 0, "case", "en", "cardinal", "1", SerializedRandomValue.from_python(1))


def test_compare_statuses_and_shapes():
    c = case()
    text = lambda value: ExecutionResult.text_result(value)
    error = ExecutionResult.exception_result(ValueError("bad"))
    assert compare_results(c, text("one"), text("one")).status == "match"
    assert compare_results(c, text("one and"), text("one")).status == "mismatch"
    assert compare_results(c, error, text("one")).status == "oracle-error"
    assert compare_results(c, text("one"), error).status == "numeralform-error"
    assert compare_results(c, error, error).status == "both-error"
    assert difference_shape("twenty-one", "twenty one") == "hyphenation only"
    assert difference_shape("É", "E\u0301") == "Unicode normalization difference"
