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
        (
            case(locale="es", kind="decimal", value=Decimal("1.10")),
            "uno punto uno",
            "uno punto uno cero",
            "decimal-trailing-zero-precision",
        ),
        (
            case(locale="es", kind="ordinal", value=20),
            "vigesimo",
            "vigésimo",
            "oracle:es-ordinal-accent",
        ),
        (
            case(locale="es", kind="ordinal", value=21),
            "vigesimoprimero",
            "vigésimo primero",
            "variant:es-ordinal-compound-orthography",
        ),
        (
            case(locale="es", kind="ordinal", value=2024),
            "dosmilésimo vigesimocuarto",
            "dosmilésimo vigésimo cuarto",
            "variant:es-ordinal-compound-orthography",
        ),
        (
            case(
                locale="es",
                kind="ordinal",
                value=121,
                options={"gender": "f"},
            ),
            "centésima vigesimoprimera",
            "centésima vigésima primera",
            "variant:es-ordinal-compound-orthography",
        ),
        (
            case(locale="es", kind="ordinal", value=12),
            "decimosegundo",
            "duodécimo",
            "variant:es-ordinal-synonym",
        ),
        (
            case(locale="fr-BE", value=951),
            "neuf cents cinquante et un",
            "neuf cent cinquante et un",
            "oracle:fr-cent-overpluralization",
        ),
        (
            case(locale="it", value=180),
            "centottanta",
            "centoottanta",
            "variant:it-cento-elision",
        ),
        (
            case(locale="ja", kind="ordinal_num", value=6836),
            "6836番目",
            "第6836",
            "variant:ja-ordinal-notation",
        ),
        (
            case(locale="sv", value=40),
            "förtio",
            "fyrtio",
            "oracle:sv-number-orthography",
        ),
        (
            case(
                locale="ru", kind="currency", value=Decimal("1079.24"), currency="EUR"
            ),
            "одна тысяча семьдесят девять евро, 24 цента",
            "одна тысяча семьдесят девять евро и 24 цента",
            "ru-eur-currency",
        ),
        (
            case(locale="en", kind="currency", value=Decimal("1.01"), currency="CAD"),
            "one dollar and 01 cents",
            "one Canadian dollar and 01 cents",
            "en-cad-currency",
        ),
        (
            case(locale="en", kind="year", value=193),
            "one ninety-three",
            "one hundred and ninety-three",
            "en-year-reading",
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

    negative = compare_results(
        case(locale="es", kind="ordinal", value=13),
        ExecutionResult.text_result("decimosegundo"),
        ExecutionResult.text_result("decimotercero"),
        accept_variants=True,
    )
    assert negative.status == "mismatch"

    compound_negative = compare_results(
        case(locale="es", kind="ordinal", value=121),
        ExecutionResult.text_result("centésima vigesimoprimera"),
        ExecutionResult.text_result("centésima vigésima primero"),
        accept_variants=True,
    )
    assert compound_negative.status == "mismatch"
    compound_wrong_number = compare_results(
        case(locale="es", kind="ordinal", value=2024),
        ExecutionResult.text_result("dosmilésimo vigesimocuarto"),
        ExecutionResult.text_result("dosmilésimo vigésimo quinto"),
        accept_variants=True,
    )
    assert compound_wrong_number.status == "mismatch"

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
            case(
                locale="en-GB",
                kind="currency",
                value=Decimal("4999.25"),
                currency="HUF",
            ),
            "four thousand nine hundred and ninety-nine forint and 25 fillér",
            "four thousand nine hundred and ninety-nine forints and 25 fillers",
            "en-huf-currency",
        ),
        (
            case(
                locale="en-GB",
                kind="currency",
                value=Decimal("2780.49"),
                currency="NOK",
            ),
            "two thousand seven hundred and eighty kroner, 49 øre",
            "two thousand seven hundred and eighty Norwegian kroner and 49 øre",
            "en-nok-currency",
        ),
        (
            case(
                locale="en-GB", kind="currency", value=Decimal("1.11"), currency="SEK"
            ),
            "one krona, 11 öre",
            "one Swedish krona and 11 öre",
            "en-sek-currency",
        ),
        (
            case(
                locale="en-GB", kind="currency", value=Decimal("101.01"), currency="SAR"
            ),
            "one hundred and one saudi riyals and 01 halalah",
            "one hundred and one riyals and 01 halala",
            "en-sar-currency",
        ),
        (
            case(
                locale="es", kind="currency", value=Decimal("2563.10"), currency="GBP"
            ),
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


def test_seed_107_remaining_good_outputs_are_accepted_variants():
    examples = (
        (
            case(
                locale="es",
                kind="ordinal",
                value=11,
                options={"gender": "feminine"},
            ),
            "decimoprimera",
            "undécima",
            "variant:es-ordinal-synonym",
        ),
        (
            case(
                locale="es",
                kind="ordinal",
                value=12,
                options={"gender": "feminine"},
            ),
            "decimosegunda",
            "duodécima",
            "variant:es-ordinal-synonym",
        ),
        (
            case(
                locale="es",
                kind="ordinal",
                value=20,
                options={"gender": "feminine"},
            ),
            "vigesimo",
            "vigésima",
            "oracle:es-ordinal-accent",
        ),
        (
            case(
                locale="es",
                kind="ordinal",
                value=1,
                options={"gender": "masculine"},
            ),
            "primero",
            "primer",
            "variant:es-ordinal-attributive-apocope",
        ),
        (
            case(
                locale="es",
                kind="ordinal",
                value=3,
                options={"gender": "masculine"},
            ),
            "tercero",
            "tercer",
            "variant:es-ordinal-attributive-apocope",
        ),
        (
            case(
                locale="es",
                kind="ordinal",
                value=13,
                options={"gender": "masculine"},
            ),
            "decimotercero",
            "decimotercer",
            "variant:es-ordinal-attributive-apocope",
        ),
        (
            case(
                locale="fr-BE",
                kind="currency",
                value=Decimal("304.80"),
                currency="USD",
                options={"separator": " and"},
            ),
            "trois cents quatre dollars and quatre-vingt cents",
            "trois cent quatre dollars and quatre-vingts cents",
            "oracle:fr-number-orthography",
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


def test_seed_107_spanish_ordinal_equivalence_rules_are_narrow():
    examples = (
        (
            case(
                locale="es",
                kind="ordinal",
                value=2,
                options={"gender": "feminine"},
            ),
            "segunda",
            "segundo",
        ),
        (
            case(
                locale="es",
                kind="ordinal",
                value=1,
                options={"gender": "feminine"},
            ),
            "primera",
            "primer",
        ),
        (
            case(
                locale="es",
                kind="ordinal",
                value=4,
                options={"gender": "masculine"},
            ),
            "cuarto",
            "cuart",
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


def test_01_todo_equivalence_rules_and_negative_controls():
    def assert_variant(local_case, expected, actual, rule):
        result = compare_results(
            local_case,
            ExecutionResult.text_result(expected),
            ExecutionResult.text_result(actual),
            accept_variants=True,
        )
        assert result.status == "variant"
        assert result.equivalence_rule == rule

    assert_variant(
        case(locale="cs", value=1_000_001),
        "milion jedna",
        "jeden milion jedna",
        "variant:cs-optional-one-million",
    )
    assert_variant(
        case(locale="de", kind="ordinal", value=100),
        "hundertste",
        "einhundertste",
        "variant:de-optional-ein-ordinal",
    )
    assert_variant(
        case(locale="de", kind="year", value=4137),
        "einundvierzighundertsiebenunddreißig",
        "viertausendeinhundertsiebenunddreißig",
        "oracle:de-post-2000-year",
    )
    assert_variant(
        case(locale="es", kind="currency", value=Decimal("569.69"), currency="NOK"),
        "quinientos sesenta y nueve coronas con sesenta y nueve øre",
        "quinientas sesenta y nueve coronas noruegas con sesenta y nueve øre",
        "oracle:es-nok-gender",
    )
    assert_variant(
        case(locale="fr-BE", kind="currency", value=Decimal("7360.00"), currency="EUR"),
        "sept mille trois cents soixantième",
        "sept mille trois cent soixantième",
        "oracle:fr-number-orthography",
    )
    assert_variant(
        case(locale="it", kind="ordinal", value=2010),
        "duemiladiecesimo",
        "duemiladecimo",
        "oracle:it-ordinal-orthography",
    )
    assert_variant(
        case(locale="fi", kind="currency", value=Decimal("1.21"), currency="INR"),
        "rupiaa ja kaksikymmentäyksi paisaa",
        "Intian rupiaa ja kaksikymmentäyksi paisaa",
        "fi-inr-currency",
    )
    assert_variant(
        case(locale="pt", kind="currency", value=Decimal("1.01"), currency="AUD"),
        "um dólar e um cêntimo",
        "um dólar australiano e um cêntimo",
        "pt-aud-currency",
    )
    assert_variant(
        case(locale="pt", kind="currency", value=Decimal("14.00"), currency="EUR"),
        "catorze euros",
        "catorze euros e zero cêntimos",
        "variant:pt-zero-minor-omission",
    )
    assert_variant(
        case(locale="ru", kind="decimal", value=Decimal("-958721.5")),
        "минус девятьсот пятьдесят восемь тысяч семьсот двадцать одна целых пять десятых",
        "минус девятьсот пятьдесят восемь тысяч семьсот двадцать одна целая пять десятых",
        "oracle:ru-decimal-whole-agreement",
    )
    assert_variant(
        case(locale="sv", kind="ordinal", value=100),
        "hundrade",
        "etthundrade",
        "variant:sv-optional-ett-ordinal",
    )
    assert_variant(
        case(locale="th", kind="currency", value=Decimal("0.11"), currency="EUR"),
        "สิบเอ็ดเซนต์",
        "ศูนย์ยูโร และ สิบเอ็ดเซนต์",
        "variant:th-zero-currency-component",
    )
    assert_variant(
        case(locale="vi", value=-20),
        "không",
        "âm hai mươi",
        "oracle:vi-negative-cardinal",
    )
    assert_variant(
        case(locale="it", kind="currency", value=Decimal("1.01"), currency="GBP"),
        "una sterlina e un penny",
        "una sterlina e un pence",
        "it-gbp-currency",
    )
    assert_variant(
        case(locale="ko", kind="ordinal", value=4789),
        "사천칠백 여든아홉 번째",
        "사천칠백팔십구 번째",
        "variant:ko-ordinal-reading",
    )
    assert_variant(
        case(locale="mn", kind="ordinal", value=3),
        "гурав дугаар",
        "гуравдугаар",
        "variant:mn-ordinal-spacing",
    )
    assert_variant(
        case(locale="zh-CN", value=-13),
        "负一十三",
        "负十三",
        "variant:zh-leading-one-ten",
    )
    assert_variant(
        case(locale="sv", kind="decimal", value=Decimal("40.20")),
        "förtio komma två",
        "fyrtio komma två noll",
        "oracle:sv-number-orthography+decimal-trailing-zero-precision",
    )

    negative_cases = (
        (case(locale="cs", value=2_000_001), "dva miliony", "jeden milion jedna"),
        (case(locale="de", kind="ordinal", value=101), "hundertste", "einhundertste"),
        (
            case(locale="es", kind="currency", value=Decimal("569.69"), currency="NOK"),
            "quinientos sesenta y nueve coronas con sesenta y nueve øre",
            "cuatrocientas sesenta y nueve coronas noruegas con sesenta y nueve øre",
        ),
        (
            case(locale="pt", kind="currency", value=Decimal("14.01"), currency="EUR"),
            "catorze euros e um cêntimo",
            "catorze euros e zero cêntimos",
        ),
        (
            case(
                locale="th",
                kind="currency",
                value=Decimal("0.11"),
                currency="EUR",
                options={"separator": " and"},
            ),
            "สิบเอ็ดเซนต์",
            "ศูนย์ยูโร และ สิบเอ็ดเซนต์",
        ),
        (
            case(locale="vi", value=-20),
            "hai mươi",
            "âm hai mươi",
        ),
    )
    for local_case, expected, actual in negative_cases:
        result = compare_results(
            local_case,
            ExecutionResult.text_result(expected),
            ExecutionResult.text_result(actual),
            accept_variants=True,
        )
        assert result.status == "mismatch"


def test_numeric_ordinal_oracle_variants_are_audited():
    def assert_variant(local_case, expected, actual):
        result = compare_results(
            local_case,
            ExecutionResult.text_result(expected),
            ExecutionResult.text_result(actual),
            accept_variants=True,
        )
        assert result.status == "variant"
        assert result.equivalence_rule == "oracle:numeric-ordinal-reading"

    assert_variant(case(locale="az", kind="ordinal_num", value=19), "19-cu", "19cı")
    assert_variant(case(locale="ca", kind="ordinal_num", value=31), "31è", "31r")
    assert_variant(case(locale="hi", kind="ordinal_num", value=3), "३रा", "३वाँ")
    assert_variant(case(locale="mn", kind="ordinal_num", value=21), "21 дүгээр", "21-р")
    assert_variant(
        case(locale="tg", kind="ordinal_num", value=8992), "8992юм", "8992ум"
    )


def test_new_todo_equivalence_rules_reject_changed_semantics():
    cases = (
        (
            case(locale="it", kind="currency", value=Decimal("1.01"), currency="GBP"),
            "una sterlina e un penny",
            "una sterlina e due pence",
        ),
        (
            case(locale="zh-CN", value=20),
            "一二十",
            "二十",
        ),
        (
            case(locale="ko", kind="ordinal", value=4789),
            "사천칠백 여든아홉 번째",
            "사천칠백팔십팔 번째",
        ),
        (
            case(locale="mn", kind="ordinal", value=3),
            "гурав дугаар",
            "дөрөвдугаар",
        ),
    )
    for local_case, expected, actual in cases:
        result = compare_results(
            local_case,
            ExecutionResult.text_result(expected),
            ExecutionResult.text_result(actual),
            accept_variants=True,
        )
        assert result.status == "mismatch"


def test_seed109_comparator_repairs_accept_report_examples():
    def assert_variant(local_case, expected, actual, rule):
        result = compare_results(
            local_case,
            ExecutionResult.text_result(expected),
            ExecutionResult.text_result(actual),
            accept_variants=True,
        )
        assert result.status == "variant"
        assert result.equivalence_rule == rule

    assert_variant(
        case(locale="ro", kind="ordinal_num", value=1),
        "1-ul",
        "1-lea",
        "oracle:numeric-ordinal-reading",
    )
    for expected in ("१ला", "३रा", "४था", "६ठा"):
        assert_variant(
            case(locale="hi", kind="ordinal_num", value=int(expected[0])),
            expected,
            f"{expected[0]}वाँ",
            "oracle:numeric-ordinal-reading",
        )
    assert_variant(
        case(locale="mn", kind="ordinal", value=1),
        "нэг дүгээр",
        "нэгдүгээр",
        "variant:mn-ordinal-spacing",
    )
    assert_variant(
        case(locale="ko", kind="ordinal", value=2319),
        "이천삼백 열아홉 번째",
        "이천삼백십구 번째",
        "variant:ko-ordinal-reading",
    )


def test_seed109_comparator_repairs_reject_semantic_changes():
    def assert_mismatch(local_case, expected, actual):
        result = compare_results(
            local_case,
            ExecutionResult.text_result(expected),
            ExecutionResult.text_result(actual),
            accept_variants=True,
        )
        assert result.status == "mismatch"

    # Romanian suffix variant applies only to the value 1.
    assert_mismatch(case(locale="ro", kind="ordinal_num", value=2), "2-ul", "2-lea")
    # Hindi ordinal suffix variants must keep the same numeric body.
    assert_mismatch(case(locale="hi", kind="ordinal_num", value=3), "४ला", "३वाँ")
    # Mongolian spacing repair must not hide a different number.
    assert_mismatch(
        case(locale="mn", kind="ordinal", value=3),
        "гурав дүгээр",
        "дөрөвдүгээр",
    )
    # Korean native-tens repair must not hide a different value.
    assert_mismatch(
        case(locale="ko", kind="ordinal", value=2319),
        "이천삼백 열아홉 번째",
        "이천삼백스무 번째",
    )


def test_seed109_rule_families_accept_report_examples():
    """One positive per seed-109 rule family, with asserted rule names."""
    checks = (
        # Decimal read styles.
        (
            case(kind="decimal", value=Decimal("9.99"), locale="pl"),
            "dziewięć przecinek dziewięćdziesiąt dziewięć",
            "dziewięć przecinek dziewięć dziewięć",
            "variant:integral-fraction-reading",
        ),
        (
            case(kind="decimal", value=Decimal("763568.067"), locale="vi"),
            "bảy trăm sáu mươi ba nghìn năm trăm sáu mươi tám phẩy bảy",
            "bảy trăm sáu mươi ba nghìn năm trăm sáu mươi tám phẩy không sáu bảy",
            "variant:integral-fraction-reading",
        ),
        (
            case(kind="decimal", value=Decimal("27689.6374"), locale="az"),
            "iyirmi yeddi min altı yüz səksən doqquz nöqtə altı min üç yüz yetmiş dörd",
            "iyirmi yeddi min altı yüz səksən doqquz nöqtə altı üç yeddi dörd",
            "variant:integral-fraction-reading",
        ),
        (
            case(kind="decimal", value=Decimal("1.20"), locale="fa"),
            "یک و بیست صدم",
            "یک ممیز دو صفر",
            "oracle:fa-denominator-reading",
        ),
        (
            case(kind="decimal", value=Decimal("484099.2950"), locale="te"),
            "నాలుగు లక్ష ఎనభై నాలుగు వేయిల తొంభై తొమ్మిది బిందువు రెండు తొమ్మిది అయిదు",
            "నాలుగు లక్ష ఎనభై నాలుగు వేయిల తొంభై తొమ్మిది బిందువు రెండు తొమ్మిది అయిదు సున్న",
            "decimal-trailing-zero-precision",
        ),
        (
            case(kind="decimal", value=Decimal("1.00"), locale="zh"),
            "一",
            "一點零零",
            "decimal-trailing-zero-precision",
        ),
        # Oracle repairs.
        (
            case(locale="sl", value=485298582),
            "štiristo petinosemdeset milijon dvesto osemindevetdeset tisoč petsto dvainosemdeset",
            "štiristo petinosemdeset milijonov dvesto osemindevetdeset tisoč petsto dvainosemdeset",
            "oracle:sl-million-genitive",
        ),
        (
            case(locale="kn", value=789066754),
            "ಎಪ್ಪತ್ತೆಂಟು ಕೋಟಿ ತೊಂಬತ್ತು ಒಂದು ಲಕ್ಷ ಅರವತ್ತಾರು ಸಾವಿರ ಏಳು ನೂರ ಐವತ್ತ್ನಾಲ್ಕು",
            "ಎಪ್ಪತ್ತೆಂಟು ಕೋಟಿ ತೊಂಬತ್ತು ಲಕ್ಷ ಅರವತ್ತಾರು ಸಾವಿರ ಏಳು ನೂರ ಐವತ್ತ್ನಾಲ್ಕು",
            "oracle:kn-extra-one",
        ),
        (
            case(locale="az", value=434501592),
            "dörd yüz otuz dörd milyon beş yüz min beş yüz doxsan iki",
            "dörd yüz otuz dörd milyon beş yüz bir min beş yüz doxsan iki",
            "oracle:az-bir-omission",
        ),
        (
            case(locale="te", value=-677971926),
            "(-) అరవై ఏడు కోట్ల డెబ్బై తొమ్మిది లక్ష డెబ్బై ఒకటి వేయి తొమ్మిది వందల ఇరవై ఆరు",
            "మైనస్ అరవై ఏడు కోట్ల డెబ్బై తొమ్మిది లక్ష డెబ్బై ఒకటి వేయి తొమ్మిది వందల ఇరవై ఆరు",
            "oracle:te-parenthesized-sign",
        ),
        (
            case(locale="tr", value=-3),
            "eksiüç",
            "eksi üç",
            "oracle:tr-concatenated-negative",
        ),
        (
            case(locale="hy", value=-129430938),
            "մինուս հարյուր քսանինը հազար չորս հարյուր երեսուն հազար ինը հարյուր երեսունութ",
            "մինուս հարյուր քսանինը միլիոն չորս հարյուր երեսուն հազար ինը հարյուր երեսունութ",
            "oracle:hy-negative-million-thousands",
        ),
        (
            case(locale="ar", value=2000),
            "ألفا",
            "ألفان",
            "oracle:ar-scale-defects",
        ),
        (
            case(locale="tet", value=896903190),
            "miliaun atus ualu sianulu resin neen ho rihun atus sia tolu atus ida sianulu",
            "miliaun atus ualu sianulu resin neen rihun atus sia tolu atus ida sianulu",
            "oracle:tet-ho-conjunction",
        ),
        # Year readings.
        (
            case(kind="year", value=8501, locale="am"),
            "ሰማኒያ አምስት መቶ አንድ",
            "ስምንት ሺህ አምስት መቶ አንድ",
            "variant:split-hundreds-year",
        ),
        (
            case(kind="year", value=301, locale="da"),
            "tre hundrede et",
            "trehundrede og et",
            "variant:split-hundreds-year",
        ),
        (
            case(kind="year", value=6731, locale="zh-CN"),
            "六七三一年",
            "六七三一",
            "variant:zh-cn-year-suffix",
        ),
        # Composition rules.
        (
            case(kind="decimal", value=Decimal("767500.2654"), locale="pt"),
            "setecentos e sessenta e sete mil quinhentos vírgula dois seis cinco quatro",
            "setecentos e sessenta e sete mil e quinhentos vírgula dois seis cinco quatro",
            "variant:pt-millar-conjunction",
        ),
        (
            case(locale="eo", value=1100),
            "milcent",
            "mil cent",
            "variant:eo-milcent-compound",
        ),
    )
    for local_case, expected, actual, rule in checks:
        result = compare_results(
            local_case,
            ExecutionResult.text_result(expected),
            ExecutionResult.text_result(actual),
            accept_variants=True,
        )
        assert result.status == "variant", (rule, local_case.locale)
        assert result.equivalence_rule == rule, (rule, result.equivalence_rule)


def test_seed109_rule_families_reject_semantic_defects():
    """Negative controls: altered digits, signs, or scale words stay mismatched."""

    def assert_mismatch(local_case, expected, actual):
        result = compare_results(
            local_case,
            ExecutionResult.text_result(expected),
            ExecutionResult.text_result(actual),
            accept_variants=True,
        )
        assert result.status == "mismatch"

    # Wrong Arabic scale form (million for thousands).
    assert_mismatch(
        case(locale="sl", value=485298582),
        "štiristo petinosemdeset milijonov sto tisoč petsto dvainosemdeset",
        "štiristo petinosemdeset milijonov dvesto osemindevetdeset tisoč petsto dvainosemdeset",
    )
    # Wrong Welsh thousand gender.
    assert_mismatch(
        case(locale="cy", value=3000),
        "tri mil",
        "tair mil",
    )
    # Wrong Romanian de construction.
    assert_mismatch(
        case(locale="ro", value=21000),
        "douăzeci și unu mii",
        "douăzeci și unu de mii",
    )
    # Ukrainian scale form defect.
    assert_mismatch(
        case(locale="uk", value=21000),
        "двадцять одна тисяч",
        "двадцять одна тисяча",
    )
    # Chinese deletion of 一 outside the tens pattern.
    assert_mismatch(
        case(locale="zh-CN", value=115),
        "一十五",
        "一百一十五",
    )
    # Decimal internal-zero loss: 0.01 must not equal 0.1.
    assert_mismatch(
        case(kind="decimal", value=Decimal("0.01"), locale="pl"),
        "zero przecinek jeden",
        "zero przecinek zero jeden",
    )
    assert_mismatch(
        case(kind="decimal", value=Decimal("0.01"), locale="zh"),
        "點零一",
        "零點零一",
    )
    # Kannada extra-one must not alter a different value.
    assert_mismatch(
        case(locale="kn", value=789066754),
        "ಎಪ್ಪತ್ತೆಂಟು ಕೋಟಿ ತೊಂಬತ್ತೊಂದು ಒಂದು ಲಕ್ಷ ಅರವತ್ತಾರು ಸಾವಿರ ಏಳು ನೂರ ಐವತ್ತ್ನಾಲ್ಕು",
        "ಎಪ್ಪತ್ತೆಂಟು ಕೋಟಿ ತೊಂಬತ್ತು ಲಕ್ಷ ಅರವತ್ತಾರು ಸಾವಿರ ಏಳು ನೂರ ಐವತ್ತ್ನಾಲ್ಕು",
    )
    # Sign changes are never accepted as variants.
    assert_mismatch(
        case(locale="te", value=677971926),
        "(-) అరవై ఏడు కోట్ల డెబ్బై తొమ్మిది లక్ష డెబ్బై ఒకటి వేయి తొమ్మిది వందల ఇరవై ఆరు",
        "అరవై ఏడు కోట్ల డెబ్బై తొమ్మిది లಕ್ಷ డೆಬ್ಬೈ ಒಕಟి ವೇయಿ తೊಮ్ಮಿది ವಂದಲ ఇరವై ఆరು",
    )


def test_seed109_composed_precision_rules():
    # Component alone: precision contraction.
    result = compare_results(
        case(kind="decimal", value=Decimal("1.20"), locale="zh"),
        ExecutionResult.text_result("一點二"),
        ExecutionResult.text_result("一點二零"),
        accept_variants=True,
    )
    assert result.status == "variant"
    assert result.equivalence_rule == "decimal-trailing-zero-precision"
    # Component alone: leading-one-ten.
    result = compare_results(
        case(locale="zh", value=15),
        ExecutionResult.text_result("一十五"),
        ExecutionResult.text_result("十五"),
        accept_variants=True,
    )
    assert result.status == "variant"
    assert result.equivalence_rule == "variant:zh-leading-one-ten"
    # Composed: both differences at once.
    result = compare_results(
        case(kind="decimal", value=Decimal("-10.10"), locale="zh"),
        ExecutionResult.text_result("負一十點一"),
        ExecutionResult.text_result("負十點一零"),
        accept_variants=True,
    )
    assert result.status == "variant"
    assert result.equivalence_rule == "variant:zh-leading-one-ten"
