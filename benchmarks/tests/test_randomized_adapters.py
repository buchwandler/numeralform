from decimal import Decimal

from benchmarks.randomized.adapters import (
    run_num2words,
    run_numeralform,
    run_numeralform_compat,
)
from benchmarks.randomized.model import RandomCase, SerializedRandomValue


def make_case(kind, value, currency=None):
    return RandomCase(
        1,
        1,
        1,
        0,
        f"case-{kind}",
        "en",
        kind,
        str(value),
        SerializedRandomValue.from_python(value),
        currency,
    )


def test_num2words_dispatch_and_nfc():
    calls = []

    def fake(value, **kwargs):
        calls.append((value, kwargs))
        return "e\u0301"

    cases = [
        make_case("cardinal", 1),
        make_case("decimal", Decimal("1.20")),
        make_case("ordinal", 1),
        make_case("year", 2024),
        make_case("currency", Decimal("1.20"), "USD"),
    ]
    results = [run_num2words(case, fake) for case in cases]
    assert all(result.text == "é" for result in results)
    assert [call[1]["to"] for call in calls] == [
        "cardinal",
        "cardinal",
        "ordinal",
        "year",
        "currency",
    ]
    assert calls[-1][1]["currency"] == "USD"


def test_numeralform_decimal_and_exception_capture():
    case = make_case("decimal", Decimal("1.20"))
    seen = []
    result = run_numeralform(
        case,
        render_function=lambda value, **kwargs: seen.append((value, kwargs)) or "ok",
    )
    assert result.text == "ok"
    assert seen[0][0].fraction == "20"
    error = run_numeralform(
        case,
        render_function=lambda *args, **kwargs: (_ for _ in ()).throw(
            ValueError("bad")
        ),
    )
    assert error.outcome == "exception"
    assert error.exception_type == "ValueError"


def test_compat_adapter_uses_num2words_call_shape():
    case = make_case("currency", Decimal("1.20"), "USD")
    calls = []

    def fake(value, **kwargs):
        calls.append((value, kwargs))
        return "ok"

    result = run_numeralform_compat(case, num2words_function=fake)
    assert result.text == "ok"
    assert calls == [
        (Decimal("1.20"), {"lang": "en", "to": "currency", "currency": "USD"})
    ]


def test_num2words_invocation_is_shared_by_execution():
    from benchmarks.randomized.adapters import num2words_invocation

    case = make_case("ordinal", 3)
    value, kwargs = num2words_invocation(case)
    assert value == case.transport_value()
    assert kwargs == {"lang": "en", "to": "ordinal"}


def test_oracle_support_and_execution_share_one_path():
    from benchmarks.randomized.adapters import oracle_supports_case

    invocations = []

    def fake(value, **kwargs):
        invocations.append((value, kwargs))
        return "e\u0301"

    case = make_case("cardinal", 1)
    assert oracle_supports_case(case, fake)
    assert run_num2words(case, fake).text == "é"
    assert len(invocations) == 2
    assert invocations[0] == invocations[1]


def test_oracle_support_reports_exceptions_as_unsupported():
    from benchmarks.randomized.adapters import oracle_supports_case

    def failing(value, **kwargs):
        raise ValueError("unsupported")

    case = make_case("cardinal", 1)
    assert not oracle_supports_case(case, failing)
    result = run_num2words(case, failing)
    assert result.outcome == "exception"
    assert result.exception_type == "ValueError"


def test_empty_oracle_output_is_an_oracle_error():
    result = run_num2words(
        make_case("decimal", Decimal("0.001")), lambda *args, **kwargs: ""
    )
    assert result.outcome == "exception"
    assert result.exception_type == "ValueError"
    assert "invalid-oracle-output" in (result.exception_message or "")


def test_known_non_numeric_ordinal_oracle_output_is_an_error():
    case = make_case("ordinal_num", 119)
    case = RandomCase(
        case.schema_version,
        case.generator_version,
        case.seed,
        case.index,
        case.case_id,
        "ar",
        case.kind,
        case.surface,
        case.value,
        case.currency,
    )
    result = run_num2words(case, lambda *args, **kwargs: "مائة وتسعة عشر")
    assert result.outcome == "exception"
    assert "non-numeric" in (result.exception_message or "")
