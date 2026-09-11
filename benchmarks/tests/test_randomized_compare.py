from decimal import Decimal

from benchmarks.randomized.compare import compare_results, difference_shape
from benchmarks.randomized.model import (
    ExecutionResult,
    RandomCase,
    SerializedRandomValue,
)


def case(*, locale="en", kind="cardinal", value=1, currency=None, options=None):
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
        options=options or {},
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

def test_surface_variant_cannot_drop_an_explicit_sign():
    result = compare_results(
        case(value=-1),
        ExecutionResult.text_result("-1"),
        ExecutionResult.text_result("1"),
        accept_variants=True,
    )
    assert result.status == "mismatch"


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



def test_named_locale_equivalence_rules_and_negative_controls():
    examples = (
        (case(locale="es", kind="decimal", value=Decimal("1.10")), "uno punto uno", "uno punto uno cero", "decimal-trailing-zero-precision"),
        (case(locale="es", kind="ordinal", value=20), "vigesimo", "vigésimo", "oracle:es-ordinal-accent"),
        (case(locale="es", kind="ordinal", value=12), "decimosegundo", "duodécimo", "variant:es-ordinal-synonym"),
        (case(locale="fr-BE", value=951), "neuf cents cinquante et un", "neuf cent cinquante et un", "oracle:fr-cent-overpluralization"),
        (case(locale="it", value=180), "centottanta", "centoottanta", "variant:it-cento-elision"),
        (case(locale="ja", kind="ordinal_num", value=6836), "6836番目", "第6836", "variant:ja-ordinal-notation"),
        (case(locale="sv", value=40), "förtio", "fyrtio", "oracle:sv-number-orthography"),
        (case(locale="ru", kind="currency", value=Decimal("1079.24"), currency="EUR"), "одна тысяча семьдесят девять евро, 24 цента", "одна тысяча семьдесят девять евро и 24 цента", "ru-eur-currency"),
        (case(locale="en", kind="currency", value=Decimal("1.01"), currency="CAD"), "one dollar and 01 cents", "one Canadian dollar and 01 cents", "en-cad-currency"),
        (case(locale="en", kind="year", value=193), "one ninety-three", "one hundred and ninety-three", "en-year-reading"),
    )
    for local_case, expected, actual, rule in examples:
        result = compare_results(
            local_case,
            ExecutionResult.text_result(expected),
            ExecutionResult.text_result(actual),
            accept_variants=True,
        )
        assert result.status == "variant"
        assert result.equivalence_rule == rule

    negative = compare_results(
        case(locale="es", kind="ordinal", value=13),
        ExecutionResult.text_result("decimosegundo"),
        ExecutionResult.text_result("decimotercero"),
        accept_variants=True,
    )
    assert negative.status == "mismatch"

    malformed = compare_results(
        case(locale="fr-BE", value=951),
        ExecutionResult.text_result("neuf cents cinquante et un"),
        ExecutionResult.text_result("neuf cent troiième"),
        accept_variants=True,
    )
    assert malformed.status == "mismatch"

    wrong_value = compare_results(
        case(locale="sv", value=41),
        ExecutionResult.text_result("förtio"),
        ExecutionResult.text_result("fyrtioett"),
        accept_variants=True,
    )
    assert wrong_value.status == "mismatch"



def test_audited_oracle_and_language_variants_from_seed_103_report():
    examples = (
        (
            case(locale="de", kind="year", value=3346),
            "dreiunddreißighundertsechsundvierzig",
            "dreitausenddreihundertsechsundvierzig",
            "oracle:de-post-2000-year",
        ),
        (
            case(locale="en-GB", kind="year", value=101),
            "one oh-one",
            "one hundred and one",
            "en-year-reading",
        ),
        (
            case(locale="en-GB", kind="year", value=3005),
            "three thousand and five",
            "thirty oh five",
            "en-year-reading",
        ),
        (
            case(locale="en-GB", kind="currency", value=Decimal("4999.25"), currency="HUF"),
            "four thousand nine hundred and ninety-nine forint and 25 fillér",
            "four thousand nine hundred and ninety-nine forints and 25 fillers",
            "en-huf-currency",
        ),
        (
            case(locale="en-GB", kind="currency", value=Decimal("2780.49"), currency="NOK"),
            "two thousand seven hundred and eighty kroner, 49 øre",
            "two thousand seven hundred and eighty Norwegian kroner and 49 øre",
            "en-nok-currency",
        ),
        (
            case(locale="en-GB", kind="currency", value=Decimal("1.11"), currency="SEK"),
            "one krona, 11 öre",
            "one Swedish krona and 11 öre",
            "en-sek-currency",
        ),
        (
            case(locale="en-GB", kind="currency", value=Decimal("101.01"), currency="SAR"),
            "one hundred and one saudi riyals and 01 halalah",
            "one hundred and one riyals and 01 halala",
            "en-sar-currency",
        ),
        (
            case(locale="es", kind="currency", value=Decimal("2563.10"), currency="GBP"),
            "dos mil quinientos sesenta y tres libras, diez peniques",
            "dos mil quinientas sesenta y tres libras y diez peniques",
            "oracle:es-gbp-gender",
        ),
        (
            case(locale="fi", kind="cardinal", value=2_000_000),
            "kaksimiljoonaa",
            "kaksi miljoonaa",
            "variant:fi-compound-spacing",
        ),
        (
            case(locale="fr", kind="currency", value=Decimal("951.20"), currency="EUR"),
            "neuf cents cinquante et un euros et vingt centimes",
            "neuf cent cinquante et un euros et vingt centimes",
            "oracle:fr-cent-overpluralization",
        ),
        (
            case(locale="fr-BE", value=802_665_181),
            "huit cents deux millions six cents soixante-cinq mille cent quatre-vingt et un",
            "huit cent deux millions six cent soixante-cinq mille cent quatre-vingt-un",
            "oracle:fr-number-orthography",
        ),
        (
            case(locale="it", kind="year", value=7603),
            "settemilaseicentotre",
            "settemilaseicentotré",
            "oracle:it-number-orthography",
        ),
        (
            case(locale="ko", kind="ordinal_num", value=3581),
            "3581 번째",
            "3581번째",
            "variant:ko-ordinal-spacing",
        ),
        (
            case(locale="pt", kind="ordinal", value=400),
            "quadrigentésimo",
            "quadringentésimo",
            "variant:pt-ordinal-orthography",
        ),
        (
            case(locale="ru", kind="currency", value=Decimal("20.15"), currency="RUB"),
            "двадцать рублей, пятнадцать копеек",
            "двадцать рублей и пятнадцать копеек",
            "ru-rub-currency",
        ),
        (
            case(locale="sv", kind="ordinal", value=20),
            "tjugode",
            "tjugonde",
            "oracle:sv-ordinal-orthography",
        ),
        (
            case(locale="th", kind="currency", value=Decimal("12.34"), currency="USD"),
            "สิบสองดอลลาร์สหรัฐสามสิบสี่เซนต์",
            "สิบสองดอลลาร์สหรัฐและสามสิบสี่เซนต์",
            "variant:th-currency-connector",
        ),
        (
            case(locale="vi", value=-19),
            "một",
            "âm mười chín",
            "oracle:vi-negative-cardinal",
        ),
    )
    for local_case, expected, actual, rule in examples:
        result = compare_results(
            local_case,
            ExecutionResult.text_result(expected),
            ExecutionResult.text_result(actual),
            accept_variants=True,
        )
        assert result.status == "variant"
        assert result.equivalence_rule == rule


def test_new_equivalence_rules_do_not_hide_known_numeralform_defects():
    examples = (
        (
            case(locale="de", kind="currency", value=Decimal("-2.01"), currency="USD"),
            "minus zwei Dollar and ein Cent",
            "zwei Dollar and ein Cent",
        ),
        (
            case(locale="fr", value=480_000_000),
            "quatre cent quatre-vingts millions",
            "quatre cent quatre-vingt millions",
        ),
        (
            case(locale="fr-DZ", value=500_000),
            "cinq cent mille",
            "cinq cents mille",
        ),
        (
            case(locale="it", value=457_233_272),
            "quattrocentocinquantasette milioni e duecentotrentatremiladuecentosettantadue",
            "quattrocentocinquantasette milioni e duecentotrentatrémiladuecentosettantadue",
        ),
        (
            case(locale="it", value=813),
            "ottocentotredici",
            "ottocentodiecitré",
        ),
        (
            case(
                locale="th",
                kind="currency",
                value=Decimal("12.34"),
                currency="USD",
                options={"separator": " and"},
            ),
            "สิบสองดอลลาร์สหรัฐสามสิบสี่เซนต์",
            "สิบสองดอลลาร์สหรัฐและสามสิบสี่เซนต์",
        ),
    )
    for local_case, expected, actual in examples:
        result = compare_results(
            local_case,
            ExecutionResult.text_result(expected),
            ExecutionResult.text_result(actual),
            accept_variants=True,
        )
        assert result.status == "mismatch"
