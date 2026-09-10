from __future__ import annotations

import subprocess
import sys
import textwrap
from decimal import Decimal

import pytest

from numeralform import DigitSequence, NumeralFormError, render, render_currency
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
    assert render(9999, locale="fi") == "yhdeksäntuhatta yhdeksänsataayhdeksänkymmentäyhdeksän"
    with pytest.raises(UnsupportedMorphologyError):
        render(1, locale="fi", case="genitive")
    with pytest.raises(InvalidValueError):
        render(10_000, locale="fi")


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
    assert "treinta y un céntimos" in render_currency(Decimal("0.31"), locale="es", currency="EUR")
    assert "dva eura" in render_currency(Decimal("2.02"), locale="cs", currency="EUR")
    assert "centy" in render_currency(Decimal("2.02"), locale="cs", currency="EUR")
    assert render_currency(Decimal("1.20"), locale="ko", currency="USD") == "일 달러 이십 센트"
    assert "หนึ่งยูโร" in render_currency(Decimal("1.20"), locale="th", currency="EUR")
    assert " und " in render_currency(Decimal("1.20"), locale="de", currency="EUR")
    assert " et " in render_currency(Decimal("1.20"), locale="fr", currency="EUR")


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
    assert render(1828, locale="de", form="year") == "eintausendachthundertachtundzwanzig"
    assert render(2024, locale="ko", form="year") == "이천이십사년"
    assert render(2024, locale="ja", form="year") == "二千二十四"
