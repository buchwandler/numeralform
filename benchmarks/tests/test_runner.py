from __future__ import annotations

from benchmarks.validation.check import check_cases
from benchmarks.validation.model import (
    CompatInvocation,
    SerializedCompatValue,
    ValidationCase,
)


def test_compatibility_cases_dispatch_through_adapter():
    case = ValidationCase(
        "compat:en:cardinal:42",
        None,
        "forty-two",
        target="compat:num2words-0.5.14",
        invocation=CompatInvocation(
            "num2words",
            (SerializedCompatValue.from_python(42),),
            {
                "lang": SerializedCompatValue.from_python("en"),
                "to": SerializedCompatValue.from_python("cardinal"),
            },
        ),
    )
    mismatches, matches, _ = check_cases([case])
    assert mismatches == []
    assert matches == 1
