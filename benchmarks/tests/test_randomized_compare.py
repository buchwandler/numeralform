from decimal import Decimal

from benchmarks.randomized.compare import compare_results, difference_shape
from benchmarks.randomized.model import (
    ExecutionResult,
    RandomCase,
    SerializedRandomValue,
)


def case(*, locale="en", kind="cardinal", value=1, currency=None):
    return RandomCase(
        1,
        1,
        1,
        0,
        "case",
        locale,
        kind,
        str(value),
        SerializedRandomValue.from_python(value),
        currency,
    )


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


def test_surface_only_differences_are_accepted_variants():
    result = compare_results(
        case(),
        ExecutionResult.text_result("twenty-one"),
        ExecutionResult.text_result("twenty one"),
        accept_variants=True,
    )
    assert result.status == "variant"
    assert result.equivalence_rule == "surface:hyphenation only"


def test_english_year_readings_are_accepted_variants():
    for value, oracle, canonical in (
        (2003, "two thousand and three", "two thousand three"),
        (1001, "one thousand and one", "ten oh one"),
    ):
        result = compare_results(
            case(kind="year", value=value),
            ExecutionResult.text_result(oracle),
            ExecutionResult.text_result(canonical),
            accept_variants=True,
        )
        assert result.status == "variant"
        assert result.equivalence_rule == "en-year-reading"


def test_english_decimal_trailing_zero_precision_is_accepted():
    for value, oracle, canonical in (
        (Decimal("1.20"), "one point two", "one point two zero"),
        (Decimal("1.00"), "one", "one point zero zero"),
        (Decimal("10.10"), "ten point one", "ten point one zero"),
    ):
        result = compare_results(
            case(kind="decimal", value=value),
            ExecutionResult.text_result(oracle),
            ExecutionResult.text_result(canonical),
            accept_variants=True,
        )
        assert result.status == "variant"
        assert result.equivalence_rule == "en-decimal-trailing-zero-precision"


def test_english_decimal_trailing_zero_precision_negative_controls():
    for value, oracle, canonical in (
        (Decimal("10.01"), "ten point one", "ten point zero one"),
        (Decimal("1.20"), "one point two", "one point two one"),
    ):
        result = compare_results(
            case(kind="decimal", value=value),
            ExecutionResult.text_result(oracle),
            ExecutionResult.text_result(canonical),
            accept_variants=True,
        )
        assert result.status == "mismatch"


def test_jpy_semantic_difference_is_not_accepted_as_text_variant():
    result = compare_results(
        case(kind="currency", value=Decimal("61.50"), currency="JPY"),
        ExecutionResult.text_result("sixty-one yen, fifty sen"),
        ExecutionResult.text_result("sixty-two yen"),
        accept_variants=True,
    )
    assert result.status == "mismatch"


def test_english_eur_currency_is_an_accepted_variant():
    result = compare_results(
        case(kind="currency", value=Decimal("3327.34"), currency="EUR"),
        ExecutionResult.text_result(
            "three thousand, three hundred and twenty-seven euro, thirty-four cents"
        ),
        ExecutionResult.text_result(
            "three thousand three hundred and twenty-seven euros and thirty-four cents"
        ),
        accept_variants=True,
    )
    assert result.status == "variant"
    assert result.equivalence_rule == "en-eur-currency"


def test_czech_eur_inflection_is_an_accepted_variant():
    result = compare_results(
        case(locale="cs", kind="currency", value=Decimal("7170.28"), currency="EUR"),
        ExecutionResult.text_result("sedm tisíc sto sedmdesát euro, dvacet osm centů"),
        ExecutionResult.text_result("sedm tisíc sto sedmdesát eur a dvacet osm centů"),
        accept_variants=True,
    )
    assert result.status == "variant"
    assert result.equivalence_rule == "cs-eur-currency"


def test_cross_language_currency_fallback_is_not_hidden():
    result = compare_results(
        case(locale="de", kind="currency", value=Decimal("8938.50"), currency="GBP"),
        ExecutionResult.text_result(
            "achttausendneunhundertachtunddreißig Pfund und fünfzig Pence"
        ),
        ExecutionResult.text_result(
            "achttausendneunhundertachtunddreißig pounds und fünfzig pence"
        ),
    )
    assert result.status == "mismatch"


def test_variant_policy_is_opt_in_for_compatibility_target():
    result = compare_results(
        case(kind="year", value=2003),
        ExecutionResult.text_result("two thousand and three"),
        ExecutionResult.text_result("two thousand three"),
    )
    assert result.status == "mismatch"
