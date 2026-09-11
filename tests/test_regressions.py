from __future__ import annotations

import subprocess
import sys
import textwrap
from decimal import Decimal

import pytest

from numeralform import (
    DigitSequence,
    NumeralFormError,
    render,
    render_currency,
    supports_currency,
)
from numeralform.errors import InvalidValueError, UnsupportedMorphologyError


def test_spanish_digit_gender_is_rejected():
    with pytest.raises(UnsupportedMorphologyError):
        render(DigitSequence("12"), locale="es", gender="feminine")


def test_spanish_digit_attributive_syntax_is_rejected():
    with pytest.raises(UnsupportedMorphologyError):
        render(DigitSequence("12"), locale="es", syntax="attributive")


def test_russian_digit_gender_is_rejected():
    with pytest.raises(UnsupportedMorphologyError):
        render(DigitSequence("12"), locale="ru", gender="feminine")


def test_russian_decimal_gender_is_rejected():
    from numeralform import DecimalNumber

    with pytest.raises(UnsupportedMorphologyError):
        render(DecimalNumber("1", "2"), locale="ru", gender="feminine")


def test_english_digit_style_is_rejected():
    with pytest.raises(NumeralFormError):
        render(DigitSequence("12"), locale="en", style="british-and")


def test_spanish_ordinal_outside_reviewed_range_is_package_error():
    with pytest.raises(NumeralFormError):
        render(30, locale="es", form="ordinal")


def test_russian_ordinal_expands_beyond_initial_review_range():
    assert render(30, locale="ru", form="ordinal") == "тридцатый"


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (1, "un"),
        (21, "veintiún"),
        (31, "treinta y un"),
        (101, "ciento un"),
        (121, "ciento veintiún"),
        (131, "ciento treinta y un"),
        (221, "doscientos veintiún"),
        (1001, "mil un"),
        (1021, "mil veintiún"),
    ],
)
def test_spanish_masculine_apocopation_composes(value, text):
    assert render(value, locale="es", syntax="attributive", gender="masculine") == text


def test_locale_owned_numeric_ordinals_match_capabilities():
    from numeralform import capabilities, supports
    from numeralform.model import NumeralForm

    assert NumeralForm.ORDINAL_NUMERIC in capabilities("en").forms
    assert supports("es", form="ordinal_num", value=5)
    assert render(5, locale="en", form="ordinal_num") == "5th"
    assert render(1, locale="fr", form="ordinal_num") == "1er"
    assert render(5, locale="fr", form="ordinal_num") == "5me"
    assert render(5, locale="es", form="ordinal_num", gender="feminine") == "5ª"


def test_finnish_capabilities_match_reviewed_domain():
    assert render(1, locale="fi") == "yksi"
    assert render(12, locale="fi") == "kaksitoista"
    assert render(42, locale="fi") == "neljäkymmentäkaksi"
    assert render(100, locale="fi") == "sata"
    assert render(1000, locale="fi") == "tuhat"
    assert render(21, locale="fi") == "kaksikymmentäyksi"
    assert render(201, locale="fi") == "kaksisataayksi"
    assert (
        render(9999, locale="fi")
        == "yhdeksäntuhatta yhdeksänsataayhdeksänkymmentäyhdeksän"
    )
    with pytest.raises(UnsupportedMorphologyError):
        render(1, locale="fi", case="genitive")
    assert render(10_000, locale="fi") == "kymmenentuhatta"

def test_finnish_ordinals_cover_hundreds_and_thousands():
    assert render(200, locale="fi", form="ordinal") == "kahdessadas"
    assert render(999, locale="fi", form="ordinal") == (
        "yhdeksässadasyhdeksäskymmenesyhdeksäs"
    )
    assert render(1000, locale="fi", form="ordinal") == "tuhannes"
    assert render(2024, locale="fi", form="ordinal") == (
        "kahdestuhannes kahdeskymmenesneljäs"
    )
    assert render(9999, locale="fi", form="ordinal") == (
        "yhdeksästuhannes yhdeksässadasyhdeksäskymmenesyhdeksäs"
    )


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (1_000, "одна тысяча"),
        (2_000, "две тысячи"),
        (4_000, "четыре тысячи"),
        (5_000, "пять тысяч"),
        (11_000, "одиннадцать тысяч"),
        (21_000, "двадцать одна тысяча"),
        (22_000, "двадцать две тысячи"),
        (25_000, "двадцать пять тысяч"),
        (1_000_000, "один миллион"),
        (2_000_000, "два миллиона"),
        (5_000_000, "пять миллионов"),
        (21_000_000, "двадцать один миллион"),
        (22_000_000, "двадцать два миллиона"),
        (25_000_000, "двадцать пять миллионов"),
    ],
)
def test_russian_scale_plural_categories(value, text):
    assert render(value, locale="ru") == text


def test_english_scale_overflow_is_rejected():
    with pytest.raises(InvalidValueError):
        render(10**12, locale="en")


def test_custom_registration_does_not_suppress_builtins():
    script = textwrap.dedent(
        """
        from numeralform import locales, register_locale, render

        class CustomRenderer:
            locale = "xx"

            @staticmethod
            def capabilities():
                from numeralform.locale import LocaleCapabilities
                from numeralform.model import NumeralForm
                return LocaleCapabilities(forms={NumeralForm.CARDINAL})

            @staticmethod
            def render(request):
                from numeralform.model import NumeralResult
                return NumeralResult("custom", request.locale, request.form, request.style, request.morphology)

        register_locale("xx", CustomRenderer)
        assert "xx" in locales()
        assert "en" in locales()
        assert render(1, locale="xx") == "custom"
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", script], check=True, capture_output=True, text=True
    )
    assert completed.stdout == ""


def test_registration_and_executable_support_are_distinct():
    from numeralform import is_registered, supports
    from numeralform.model import NumeralForm

    assert is_registered("ar")
    assert not supports("ar")
    assert supports("en")
    assert supports("en", form=NumeralForm.CARDINAL, value=42)
    assert supports("en", form=NumeralForm.ORDINAL_NUMERIC)


def test_profile_details_are_deterministic():
    completed = subprocess.run(
        [sys.executable, "-m", "numeralform.cli", "--capabilities", "es"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert '"profiles"' in completed.stdout
    assert completed.stdout.index('"form": "cardinal"') < completed.stdout.index(
        '"form": "decimal"'
    )


def test_supported_num2words_mappings():
    from numeralform.compat import num2words

    assert num2words(42, lang="en") == "forty-two"
    assert num2words(42, lang="en", to="ordinal") == "forty-second"
    assert num2words(2024, lang="en", to="year") == "twenty twenty-four"


def test_unknown_legacy_options_fail():
    from numeralform.compat import num2words

    with pytest.raises(NumeralFormError):
        num2words(42, currency="EUR")


@pytest.mark.parametrize(
    ("locale", "value", "text"),
    (
        ("pt", 200, "duzentos"),
        ("pt", 2000, "dois mil"),
        ("pt", 100000, "cem mil"),
        ("pt", 2_000_000, "dois milhões"),
        ("cs", 99, "devadesát devět"),
        ("cs", 2000, "dva tisíce"),
        ("th", 99999, "เก้าหมื่นเก้าพันเก้าร้อยเก้าสิบเก้า"),
        ("th", 100001, "หนึ่งแสนเอ็ด"),
        ("de", 2_000_000, "zwei Millionen"),
        ("it", 1001, "milleuno"),
        ("it", 1_000_001, "un milione e uno"),
        ("fi", 21, "kaksikymmentäyksi"),
        ("ko", 2009, "이천구년"),
        ("sv", 1999, "etttusen niohundranittionio"),
        ("fr", 80000, "quatre-vingt mille"),
        ("vi", 1_000_001, "một triệu lẻ một"),
    ),
)
def test_random_report_renderer_regressions(locale, value, text):
    form = "year" if locale == "ko" else "cardinal"
    assert render(value, locale=locale, form=form) == text


def test_currency_locale_morphology_and_joining():
    assert "центов" in render_currency(Decimal("0.38"), locale="ru", currency="EUR")
    assert "treinta y un céntimos" in render_currency(
        Decimal("0.31"), locale="es", currency="EUR"
    )
    assert "dva eura" in render_currency(Decimal("2.02"), locale="cs", currency="EUR")
    assert "centy" in render_currency(Decimal("2.02"), locale="cs", currency="EUR")
    assert (
        render_currency(Decimal("1.20"), locale="ko", currency="USD")
        == "일달러 이십센트"
    )
    assert "หนึ่งยูโร" in render_currency(Decimal("1.20"), locale="th", currency="EUR")
    assert " und " in render_currency(Decimal("1.20"), locale="de", currency="EUR")
    assert render_currency(Decimal("8938.50"), locale="de", currency="GBP").endswith(
        "Pfund und fünfzig Pence"
    )
    assert render_currency(Decimal("5532.49"), locale="de", currency="USD").endswith(
        "Dollar und neunundvierzig Cent"
    )
    assert " et " in render_currency(Decimal("1.20"), locale="fr", currency="EUR")


def test_german_currency_uses_attributive_terminal_ein():
    assert render(1, locale="de") == "eins"
    assert render(301, locale="de") == "dreihunderteins"
    assert (
        render_currency(Decimal("301.58"), locale="de", currency="EUR")
        == "dreihundertein Euro und achtundfünfzig Cent"
    )
    assert (
        render_currency(Decimal("1341.01"), locale="de", currency="EUR")
        == "eintausenddreihunderteinundvierzig Euro und ein Cent"
    )
    assert (
        render_currency(Decimal("501.72"), locale="de", currency="GBP")
        == "fünfhundertein Pfund und zweiundsiebzig Pence"
    )
    assert (
        render_currency(Decimal("4216.01"), locale="de", currency="GBP")
        == "viertausendzweihundertsechzehn Pfund und ein Penny"
    )
    assert (
        render_currency(Decimal("6401.30"), locale="de", currency="USD")
        == "sechstausendvierhundertein Dollar und dreißig Cent"
    )
    assert (
        render_currency(Decimal("1.01"), locale="de", currency="EUR")
        == "ein Euro und ein Cent"
    )
    assert (
        render_currency(Decimal("21.21"), locale="de", currency="EUR")
        == "einundzwanzig Euro und einundzwanzig Cent"
    )
    assert (
        render_currency(Decimal("101.11"), locale="de", currency="EUR")
        == "einhundertein Euro und elf Cent"
    )


def test_canonical_ordinal_stems_and_compounds():
    assert render(11, locale="de", form="ordinal") == "elfte"
    assert render(13, locale="de", form="ordinal") == "dreizehnte"
    assert render(88, locale="fi", form="ordinal") == "kahdeksaskymmeneskahdeksas"
    assert render(54, locale="fr", form="ordinal") == "cinquante-quatrième"
    assert render(50, locale="it", form="ordinal") == "cinquantesimo"
    assert render(57, locale="it", form="ordinal") == "cinquantasettesimo"
    assert render(11, locale="pt", form="ordinal") == "décimo primeiro"
    assert render(23, locale="ru", form="ordinal") == "двадцать третий"
    assert render(42, locale="sv", form="ordinal") == "fyrtioandra"


def test_canonical_year_policies():
    assert render(1828, locale="de", form="year") == "achtzehnhundertachtundzwanzig"
    assert render(1099, locale="de", form="year") == "eintausendneunundneunzig"
    assert render(1100, locale="de", form="year") == "elfhundert"
    assert render(1900, locale="de", form="year") == "neunzehnhundert"
    assert render(1999, locale="de", form="year") == "neunzehnhundertneunundneunzig"
    assert render(2000, locale="de", form="year") == "zweitausend"
    assert render(2024, locale="ko", form="year") == "이천이십사년"
    assert render(2024, locale="ja", form="year") == "二千二十四年"


def test_finnish_large_scale_cardinals():
    assert render(1_000, locale="fi") == "tuhat"
    assert render(2_000, locale="fi") == "kaksituhatta"
    assert render(1_000_000, locale="fi") == "miljoona"
    assert render(2_000_000, locale="fi") == "kaksi miljoonaa"
    assert render(31_000_000, locale="fi") == "kolmekymmentäyksi miljoonaa"
    assert render(386_130_945, locale="fi") == (
        "kolmesataakahdeksankymmentäkuusi miljoonaa "
        "satakolmekymmentätuhatta yhdeksänsataaneljäkymmentäviisi"
    )


def test_01_todo_renderer_regressions():
    assert render(31_000_000, locale="cs") == "třicet jedna milionů"
    assert render(19, locale="de", form="ordinal") == "neunzehnte"
    assert render(21, locale="de", form="ordinal") == "einundzwanzigste"
    assert render(119, locale="de", form="ordinal") == "einhundertneunzehnte"
    assert render(5319, locale="de", form="ordinal") == "fünftausenddreihundertneunzehnte"
    assert render(100, locale="de", form="ordinal") == "einhundertste"
    assert render(3, locale="fr", form="ordinal") == "troisième"
    assert render(9, locale="fr", form="ordinal") == "neuvième"
    assert render(31, locale="fr-BE", form="ordinal") == "trente et unième"
    assert render(2209, locale="fr", form="ordinal") == "deux mille deux cent neuvième"
    assert render(23, locale="it") == "ventitré"
    assert render(3163, locale="it") == "tremilacentosessantatré"
    assert render(7245, locale="it", form="ordinal") == "settemiladuecentoquarantacinquesimo"
    assert render(1188, locale="pt", form="ordinal") == "milésimo centésimo octogésimo oitavo"
    assert render(1800, locale="pt") == "mil e oitocentos"
    assert render(1801, locale="pt-BR") == "mil oitocentos e um"
    assert render(578_990_689, locale="ko") == "오억 칠천팔백구십구만 육백팔십구"
    assert render(5455, locale="ko", form="ordinal_num") == "5455번째"
    assert render(101, locale="vi") == "một trăm lẻ một"
    assert render(1050, locale="vi") == "một nghìn lẻ năm mươi"


def test_audited_scale_and_morphology_regressions():
    assert render(684_012_070, locale="pt") == (
        "seiscentos e oitenta e quatro milhões e doze mil e setenta"
    )
    assert render(-10_000, locale="ko") == "마이너스 만"
    assert render(104_253_995, locale="ko") == (
        "일억 사백이십오만 삼천구백구십오"
    )
    assert render(Decimal("32.11"), locale="ru", form="decimal") == (
        "тридцать две целых одиннадцать сотых"
    )
    assert render(76, locale="fr", form="ordinal") == "soixante-seizième"
    assert render(871, locale="fr-BE", form="ordinal") == "huit cent septante et unième"
    assert render(408, locale="it", form="ordinal") == "quattrocentottesimo"



def test_01_todo_runtime_examples():
    assert render(3000, locale="en-GB", form="year") == "three thousand"
    assert render(5000, locale="en-NG", form="year") == "five thousand"
    assert render(1_000_000, locale="fi") == "miljoona"
    assert render(0, locale="fi", form="ordinal") == "nollas"
    assert render_currency(Decimal("1.01"), locale="fi", currency="GBP").endswith(
        "yksi pennyä"
    )
    assert render_currency(Decimal("1.21"), locale="fi", currency="INR").endswith(
        "kaksikymmentäyksi paisaa"
    )
    assert render(77, locale="fr", form="ordinal") == "soixante-dix-septième"
    assert render(99, locale="fr", form="ordinal") == "quatre-vingt-dix-neuvième"
    assert render(653_000_000, locale="it").startswith(
        "seicentocinquantatré milioni"
    )
    assert "trémila" not in render(273_000, locale="it")
    assert render_currency(Decimal("0.61"), locale="it", currency="EUR").endswith(
        "sessantun centesimi"
    )
    assert render_currency(-100, locale="ja", currency="JPY") == "マイナス百円"
    assert render(812_000_864, locale="pt") == (
        "oitocentos e doze milhões oitocentos e sessenta e quatro"
    )
    assert render(935_100_674, locale="pt") == (
        "novecentos e trinta e cinco milhões e cem mil "
        "seiscentos e setenta e quatro"
    )
    assert "cêntimo" in render_currency(Decimal("1.01"), locale="pt", currency="AUD")
    assert "péni" in render_currency(Decimal("1.01"), locale="pt", currency="GBP")
    assert render(Decimal("722124.81"), locale="ru", form="decimal").endswith(
        "восемьдесят одна сотая"
    )
def test_localized_currency_support_and_morphology():
    assert supports_currency("es", "CAD")
    assert supports_currency("fi", "AUD")
    assert supports_currency("pt", "CAD")
    assert not supports_currency("fi", "CHF")
    assert "una libra" in render_currency(Decimal("1.00"), locale="es", currency="GBP")
    assert "one paisa" in render_currency(Decimal("1.01"), locale="en", currency="INR")

def test_audited_currency_sign_gender_regional_and_attachment_fixes():
    assert render_currency(Decimal("-2.01"), locale="de", currency="USD") == (
        "minus zwei Dollar und ein Cent"
    )
    assert render_currency(Decimal("-1.00"), locale="fr", currency="EUR").startswith(
        "moins un euro"
    )
    assert render_currency(Decimal("-99.00"), locale="ko", currency="JPY") == (
        "마이너스 구십구엔"
    )
    assert render_currency(Decimal("992.00"), locale="es", currency="NOK") == (
        "novecientas noventa y dos coronas noruegas con cero øre"
    )
    assert render_currency(Decimal("20.15"), locale="ru", currency="RUB") == (
        "двадцать рублей и пятнадцать копеек"
    )
    assert render_currency(Decimal("1.00"), locale="ja", currency="JPY") == "一円"
    assert "cêntimo" in render_currency(Decimal("2.01"), locale="pt-PT", currency="AUD")
    assert "péni" in render_currency(Decimal("1.01"), locale="pt-PT", currency="GBP")

def test_audited_locale_grammar_fixes():
    assert render(113, locale="en-GB", form="ordinal") == "one hundred and thirteenth"
    assert render(3048, locale="en-GB", form="ordinal") == "three thousand and forty-eighth"
    assert render(4685, locale="en-GB", form="ordinal") == (
        "four thousand six hundred and eighty-fifth"
    )
    assert render(1_000_001, locale="en-IN") == "ten lakh and one"
    assert render(684_012_070, locale="pt") == (
        "seiscentos e oitenta e quatro milhões e doze mil e setenta"
    )
    assert render(684_012_070, locale="pt-BR") == (
        "seiscentos e oitenta e quatro milhões e doze mil e setenta"
    )
    assert render(20, locale="es", form="ordinal", gender="feminine", syntax="attributive") == "vigésima"
    assert render(13, locale="es", form="ordinal") == "decimotercero"
    assert render(84, locale="fr", form="ordinal") == "quatre-vingt-quatrième"
    assert render(101, locale="fr", form="ordinal") == "cent unième"
    assert render(480_000_000, locale="fr") == "quatre cent quatre-vingts millions"
    assert render(33, locale="ru", form="ordinal") == "тридцать третий"
    assert render(103, locale="ru", form="ordinal") == "сто третий"
    assert render(-400_000_000, locale="ko") == "마이너스 사억"
    assert render(813, locale="it") == "ottocentotredici"
    assert "trémila" not in render(273_000, locale="it")
    assert render(1001, locale="it", form="ordinal") == "milleunesimo"
    assert render(1_000_000, locale="cs") == "jeden milion"
