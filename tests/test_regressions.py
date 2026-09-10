from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from numeralform import DigitSequence, NumeralFormError, render
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
    assert render(42, locale="fi") == "neljäkymmentä kaksi"
    assert render(100, locale="fi") == "sata"
    assert render(1000, locale="fi") == "tuhat"
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
