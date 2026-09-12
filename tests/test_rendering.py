from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

import pytest

from numeralform import (
    Case,
    DecimalNumber,
    DigitSequence,
    FractionNumber,
    Gender,
    Morphology,
    NumeralForm,
    NumeralRequest,
    Syntax,
    UnsupportedMorphologyError,
    canonicalize_locale,
    capabilities,
    fallback_chain,
    locales,
    realize,
    render,
    resolve_locale,
    supports,
)


def test_exports_and_request_result():
    request = NumeralRequest(
        21,
        "es-MX",
        syntax=Syntax.ATTRIBUTIVE,
        morphology=Morphology(gender=Gender.MASCULINE),
    )
    result = realize(request)
    assert result.text == "veintiún"
    assert result.locale == "es-MX"
    assert result.requested_locale == "es-MX"
    assert result.form == NumeralForm.CARDINAL


def test_primitive_convenience_inputs():
    assert render(Decimal("1.20"), locale="en") == "one point two zero"
    assert render(Fraction(1, 2), locale="en") == "one half"


def test_locale_normalization_and_fallback():
    assert canonicalize_locale("EN_us") == "en-US"
    assert canonicalize_locale("cn") == "zh-CN"
    assert fallback_chain("en-US") == ("en-US", "en")
    assert resolve_locale("en-US") == "en-US"
    assert resolve_locale("en-GB") == "en-GB"
    assert "en" in locales()
    assert "en-US" in locales()
    assert "en-GB" in locales()
    assert "ru" in locales()
    assert "am" in locales()
    assert "kk" in locales()


def test_capabilities_are_truthful():
    assert NumeralForm.ORDINAL in capabilities("ru").forms
    assert Gender.FEMININE in capabilities("ru").genders
    assert Case.GENITIVE in capabilities("ru").cases


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (0, "zero"),
        (1, "one"),
        (2, "two"),
        (10, "ten"),
        (11, "eleven"),
        (19, "nineteen"),
        (20, "twenty"),
        (21, "twenty-one"),
        (42, "forty-two"),
        (99, "ninety-nine"),
        (100, "one hundred"),
        (101, "one hundred one"),
        (115, "one hundred fifteen"),
        (199, "one hundred ninety-nine"),
        (200, "two hundred"),
        (999, "nine hundred ninety-nine"),
        (1000, "one thousand"),
        (1001, "one thousand one"),
        (2024, "two thousand twenty-four"),
        (1_000_000, "one million"),
        (-42, "minus forty-two"),
    ],
)
def test_english_baseline(value, text):
    assert render(value, locale="en") == text


def test_spanish_baseline_and_morphology():
    assert render(42, locale="es") == "cuarenta y dos"
    assert render(100, locale="es") == "cien"
    assert render(101, locale="es") == "ciento uno"
    assert render(1000, locale="es") == "mil"
    assert render(21, locale="es") == "veintiuno"
    assert (
        render(21, locale="es", syntax="attributive", gender="masculine") == "veintiún"
    )
    assert (
        render(21, locale="es", syntax="attributive", gender="feminine") == "veintiuna"
    )
    assert (
        render(31, locale="es", syntax="attributive", gender="masculine")
        == "treinta y un"
    )
    assert render(1, locale="es", syntax="attributive", gender="feminine") == "una"


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (70, "setenta"),
        (79, "setenta e nove"),
        (80, "oitenta"),
        (89, "oitenta e nove"),
        (90, "noventa"),
        (99, "noventa e nove"),
    ],
)
def test_portuguese_tens_boundaries(value, text):
    assert render(value, locale="pt-BR") == text
    assert render(value, locale="pt-PT") == text


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (10, "tionde"),
        (11, "elfte"),
        (12, "tolfte"),
        (13, "trettonde"),
        (14, "fjortonde"),
        (15, "femtonde"),
        (16, "sextonde"),
        (17, "sjuttonde"),
        (18, "artonde"),
        (19, "nittonde"),
    ],
)
def test_swedish_ordinal_teens(value, text):
    assert render(value, locale="sv", form="ordinal") == text


def test_russian_gender():
    assert render(1, locale="ru") == "один"
    assert render(1, locale="ru", gender="feminine") == "одна"
    assert render(1, locale="ru", gender="neuter") == "одно"
    assert render(2, locale="ru", gender="feminine") == "две"
    assert render(21, locale="ru", gender="feminine") == "двадцать одна"
    assert render(22, locale="ru", gender="feminine") == "двадцать две"
    assert render(1000, locale="ru") == "одна тысяча"


def test_digits_and_precision():
    assert render(DigitSequence("0042"), locale="en") == "zero zero four two"
    assert render(DigitSequence("0042"), locale="es") == "cero cero cuatro dos"
    assert render(DecimalNumber("1", "200"), locale="en") == "one point two zero zero"
    assert (
        render(DecimalNumber("1", "20", True), locale="ru")
        == "минус одна целая двадцать сотых"
    )


def test_forms():
    assert render(42, locale="en", form="ordinal") == "forty-second"
    assert render(42, locale="en", form="year") == "forty-two"
    assert render(FractionNumber(2, 3), locale="en") == "two thirds"
    assert render(105, locale="en", style="british-and") == "one hundred and five"


def test_unsupported_morphology_is_strict():
    with pytest.raises(UnsupportedMorphologyError):
        render(2, locale="en", case="genitive")
    assert render(2, locale="ru", case="genitive") == "двух"
    with pytest.raises(UnsupportedMorphologyError):
        render(2, locale="es", gender="neuter")


@pytest.mark.parametrize(
    ("locale", "value", "text"),
    [("es", 20, "vigésimo"), ("ru", 29, "двадцать девятый")],
)
def test_reviewed_ordinal_boundaries(locale, value, text):
    assert render(value, locale=locale, form="ordinal") == text


def test_supported_profiles_render_representative_values():
    sample_values = {
        NumeralForm.CARDINAL: (0, 1, 2, 10, 21, 42, 100, 1000),
        NumeralForm.ORDINAL: (1, 2, 10, 21, 42),
        NumeralForm.ORDINAL_NUMERIC: (1, 2, 10, 42),
        NumeralForm.YEAR: (1, 42, 2024),
        NumeralForm.DECIMAL: (DecimalNumber("12", "50"),),
        NumeralForm.FRACTION: (FractionNumber(2, 3),),
        NumeralForm.DIGITS: (DigitSequence("0042"),),
    }
    for locale in locales():
        for profile in capabilities(locale).profiles:
            for syntax in profile.syntaxes:
                for style in profile.styles:
                    for value in sample_values.get(profile.form, (42,)):
                        if supports(
                            locale,
                            form=profile.form,
                            syntax=syntax,
                            style=style,
                            value=value,
                        ):
                            assert render(
                                value,
                                locale=locale,
                                form=profile.form,
                                syntax=syntax,
                                style=style,
                            )


def test_cardinal_renderers_cover_common_numeric_paths():
    for locale in locales():
        values = range(90)
        if not locale.startswith("pt"):
            values = (*values, 99, 100, 101, 110, 999, 1000, 1001, 2024)
        for value in values:
            assert render(value, locale=locale)
