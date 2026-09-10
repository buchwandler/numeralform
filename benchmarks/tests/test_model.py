from __future__ import annotations

from decimal import Decimal

from benchmarks.validation.model import (
    CompatInvocation,
    SerializedCompatValue,
    SerializedValue,
)


def test_value_round_trips_without_precision_loss():
    values = (
        SerializedValue("int", value="0042"),
        SerializedValue("digits", value="0042"),
        SerializedValue("decimal", integer="1", fraction="20", negative=False),
        SerializedValue("fraction", numerator="2", denominator="3"),
    )
    for value in values:
        decoded = SerializedValue.from_json(value.to_json())
        assert decoded.to_json() == value.to_json()


def test_compatibility_invocation_round_trips_legacy_types():
    invocation = CompatInvocation(
        "num2words",
        (
            SerializedCompatValue.from_python(Decimal("1.20")),
            SerializedCompatValue.from_python("en"),
        ),
        {"to": SerializedCompatValue.from_python("cardinal")},
    )
    decoded = CompatInvocation.from_json(invocation.to_json())
    function, positional, kwargs = decoded.as_python()
    assert function == "num2words"
    assert positional == [Decimal("1.20"), "en"]
    assert kwargs == {"to": "cardinal"}
