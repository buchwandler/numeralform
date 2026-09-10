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
    assert [call[1]["to"] for call in calls] == ["cardinal", "cardinal", "ordinal", "year", "currency"]
    assert calls[-1][1]["currency"] == "USD"


def test_numeralform_decimal_and_exception_capture():
    case = make_case("decimal", Decimal("1.20"))
    seen = []
    result = run_numeralform(case, render_function=lambda value, **kwargs: seen.append((value, kwargs)) or "ok")
    assert result.text == "ok"
    assert seen[0][0].fraction == "20"
    error = run_numeralform(case, render_function=lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("bad")))
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
    assert calls == [(Decimal("1.20"), {"lang": "en", "to": "currency", "currency": "USD"})]
