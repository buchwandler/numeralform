# ruff: noqa: B017
from __future__ import annotations

from decimal import Decimal

import pytest

from numeralform import (
    CapabilityProfile,
    Case,
    DecimalNumber,
    DigitSequence,
    FeatureSpec,
    FractionNumber,
    Gender,
    LocaleCapabilities,
    NumeralForm,
    NumeralRequest,
    NumericDomain,
    canonicalize_locale,
    capabilities,
    fallback_chain,
    is_registered,
    locales,
    realize,
    render,
    render_request,
    resolve_locale,
    supports,
)
from numeralform.cli import main
from numeralform.compat import num2words
from numeralform.renderers.base import _features_accept, validate_request
from numeralform.renderers.generic import GenericLocaleRenderer


def test_cli_main_covers_rendering_modes(capsys):
    assert main(["--list-locales"]) == 0
    assert main(["--capabilities", "en"]) == 0
    assert main(["42", "--locale", "en"]) == 0
    assert main(["0042", "--locale", "en", "--digits"]) == 0
    assert main(["1.20", "--locale", "en", "--decimal"]) == 0
    assert main(["2/3", "--locale", "en", "--fraction"]) == 0
    assert capsys.readouterr().out


def test_generic_baseline_renderer_preserves_typed_values():
    renderer = GenericLocaleRenderer("xx")
    assert renderer.render(NumeralRequest(42, "xx")).text == "42"
    assert (
        renderer.render(
            NumeralRequest(DigitSequence("0042"), "xx", NumeralForm.DIGITS)
        ).text
        == "0042"
    )
    assert (
        renderer.render(
            NumeralRequest(DecimalNumber("1", "20"), "xx", NumeralForm.DECIMAL)
        ).text
        == "1.20"
    )
    assert (
        renderer.render(
            NumeralRequest(FractionNumber(2, 3), "xx", NumeralForm.FRACTION)
        ).text
        == "2/3"
    )
    assert renderer.render(NumeralRequest(42, "xx", NumeralForm.ORDINAL)).text == "42."


def test_chinese_compatibility_forms_and_scales():
    assert num2words(0, lang="zh") == "零"
    assert num2words(10_005, lang="zh") == "一万零五"
    assert num2words(100_000_001, lang="zh") == "一亿零一"
    assert num2words(Decimal("1.20"), lang="zh") == "一點二"
    assert num2words(2024, lang="zh", to="year") == "二零二四年"
    assert num2words(42, lang="zh", to="ordinal") == "第四十二"
    assert num2words(42, lang="zh", to="ordinal_num") == "第42"
    assert num2words(1, lang="zh", to="currency") == "一元"
    assert num2words(1.25, lang="zh", to="currency") == "一元二角五分"


def test_compatibility_option_translation_and_legacy_paths():
    assert num2words(42, lang="en", ordinal=True) == "forty-second"
    assert num2words(101, lang="en", to="year") == "one oh-one"
    assert num2words(999, lang="en", to="year") == "nine ninety-nine"
    assert num2words(1000, lang="en", to="year") == "one thousand"
    assert num2words(1, lang="en", to="ordinal_num") == "1st"
    assert num2words(1, lang="es", to="ordinal_num", gender="feminine") == "1ª"
    assert num2words(1, lang="fr", to="ordinal_num") == "1er"
    assert num2words(1, lang="eo", to="ordinal_num") == "1a"
    assert num2words(1, lang="fa", to="ordinal_num") == "1م"
    assert num2words(1, lang="ja", to="ordinal_num") == "第1"
    assert num2words(1, lang="pt", to="ordinal_num") == "1.º"
    assert num2words(1, lang="de", to="ordinal_num") == "1."


def test_supported_profiles_accept_supported_morphology():
    for locale in locales():
        for profile in capabilities(locale).profiles:
            value = {
                NumeralForm.CARDINAL: 21,
                NumeralForm.ORDINAL: 21,
                NumeralForm.ORDINAL_NUMERIC: 21,
                NumeralForm.YEAR: 2024,
                NumeralForm.DECIMAL: DecimalNumber("12", "5"),
                NumeralForm.FRACTION: FractionNumber(2, 3),
                NumeralForm.DIGITS: DigitSequence("0042"),
            }.get(profile.form, 1)
            syntax = next(iter(profile.syntaxes))
            for gender in profile.genders:
                morphology = {"gender": gender.value}
                if supports(
                    locale,
                    form=profile.form,
                    syntax=syntax,
                    morphology=morphology,
                    value=value,
                ):
                    assert render(
                        value,
                        locale=locale,
                        form=profile.form,
                        syntax=syntax,
                        gender=gender,
                    )
            for case in profile.cases:
                morphology = {"case": getattr(case, "value", case)}
                if supports(
                    locale,
                    form=profile.form,
                    syntax=syntax,
                    morphology=morphology,
                    value=value,
                ):
                    assert render(
                        value,
                        locale=locale,
                        form=profile.form,
                        syntax=syntax,
                        case=case,
                    )


def test_validation_and_conversion_error_paths():
    with pytest.raises(Exception):
        render("bad", locale="en")
    with pytest.raises(Exception):
        render(-1, locale="en", form="year")
    with pytest.raises(Exception):
        render(-1, locale="en", form="ordinal")
    with pytest.raises(Exception):
        render(1, locale="en", form="digits", features={"unknown": True})
    with pytest.raises(Exception):
        render(1, locale="en", style="missing")
    with pytest.raises(Exception):
        DigitSequence("")
    with pytest.raises(Exception):
        DigitSequence("１２")
    with pytest.raises(Exception):
        DecimalNumber("", "1")
    with pytest.raises(Exception):
        DecimalNumber("1", "")
    with pytest.raises(Exception):
        DecimalNumber("1", "2", 1)
    with pytest.raises(Exception):
        FractionNumber(1, 0)
    with pytest.raises(Exception):
        FractionNumber(True, 2)
    with pytest.raises(Exception):
        NumeralRequest(1, "")
    with pytest.raises(Exception):
        NumeralRequest(1, "en", morphology={"gender": "masculine"})
    with pytest.raises(Exception):
        canonicalize_locale("not a locale")


def test_morphology_and_feature_validation_branches():
    for kwargs in (
        {"case": "genitive"},
        {"animacy": "animate"},
        {"grammatical_number": "plural"},
        {"noun_class": "common"},
        {"definiteness": "definite"},
        {"state": "construct"},
        {"features": {"dialect": "x"}},
    ):
        with pytest.raises(Exception):
            render(1, locale="en", **kwargs)
    with pytest.raises(Exception):
        NumeralRequest(1, "en", style=" ")
    with pytest.raises(Exception):
        NumeralRequest(1, "en", features={"": True})
    with pytest.raises(Exception):
        NumeralRequest(1, "en", features={"x": 1})
    with pytest.raises(Exception):
        NumeralRequest(1, "en", features={"x": (1,)})


def test_currency_validation_branches():
    from numeralform import MoneyAmount, render_currency

    for value in (True, object(), "bad"):
        with pytest.raises(Exception):
            render_currency(value, locale="en")
    with pytest.raises(Exception):
        render_currency(1, locale="en", currency="EU")
    with pytest.raises(Exception):
        render_currency(1, locale="en", separator=1)
    with pytest.raises(Exception):
        render_currency(1, locale="en", currency="ZZZ")
    with pytest.raises(Exception):
        MoneyAmount(1, 100, "EUR")
    with pytest.raises(Exception):
        MoneyAmount(1, 0, "EUR", negative=1)
    with pytest.raises(Exception):
        MoneyAmount(1, 0, "EUR", minor_units=7)


def test_locale_capability_validation_and_fallback_branches():
    for kwargs in (
        {"minimum": True},
        {"maximum": "100"},
        {"minimum": 2, "maximum": 1},
        {"allow_negative": 1},
        {"decimals": 1},
    ):
        with pytest.raises(Exception):
            NumericDomain(**kwargs)
    with pytest.raises(Exception):
        FeatureSpec("")
    with pytest.raises(Exception):
        FeatureSpec("x", values=[""])
    with pytest.raises(Exception):
        FeatureSpec("x", boolean=True, values=["yes"])
    with pytest.raises(Exception):
        CapabilityProfile(NumeralForm.CARDINAL, cases=[None])
    with pytest.raises(Exception):
        CapabilityProfile(NumeralForm.CARDINAL, animacies=[None])
    capabilities_with_profiles = LocaleCapabilities(profiles=({"form": "cardinal"},))
    assert NumeralForm.CARDINAL in capabilities_with_profiles.forms
    legacy = LocaleCapabilities(forms={"cardinal"}, genders={"feminine"}, animacy=True)
    assert legacy.animacy
    assert fallback_chain("zh-Latn-CN-private")


def test_compatibility_option_translation_branches():
    from numeralform.compat.num2words import _apply_precision, _translate_kwargs

    assert _apply_precision(DecimalNumber("1", "25"), 1).fraction == "3"
    assert _apply_precision(1, 2).fraction == "00"
    assert (
        _translate_kwargs({"gender": "m", "case": " Genitive "})["gender"]
        == "masculine"
    )
    assert (
        _translate_kwargs({"plural": True, "animate": False})["grammatical_number"]
        == "plural"
    )
    assert (
        _translate_kwargs({"clazz": "common", "construct": True})["state"]
        == "construct"
    )
    with pytest.raises(Exception):
        _translate_kwargs({"plural": 1})
    with pytest.raises(Exception):
        _translate_kwargs({"animate": 1})
    with pytest.raises(Exception):
        _translate_kwargs({"construct": 1})


def test_base_feature_validation_paths():
    specs = (
        FeatureSpec("choice", values={"a", "b"}),
        FeatureSpec("flag", boolean=True),
        FeatureSpec("many", values={"a", "b"}),
    )
    assert _features_accept(specs, {"choice": "a", "flag": True, "many": ("a", "b")})
    assert not _features_accept(specs, {"unknown": "a"})
    assert not _features_accept(specs, {"flag": "yes"})
    assert not _features_accept(specs, {"choice": "z"})
    assert not _features_accept(specs, {"many": ("z",)})
    assert not _features_accept(specs, {"choice": 1})
    with pytest.raises(Exception):
        validate_request(
            NumeralRequest(1, "xx"),
            LocaleCapabilities(
                profiles=(
                    {
                        "form": "cardinal",
                        "features": specs,
                        "domain": {"maximum": 0},
                    },
                ),
            ),
        )


def test_structured_currency_result_path():
    from numeralform import CurrencyRequest, MoneyAmount, realize_currency

    request = CurrencyRequest(MoneyAmount(2, 5, "EUR"), "en")
    result = realize_currency(request)
    assert result.text
    assert result.request is request


def test_finnish_inflection_table_paths():
    from numeralform.renderers.fi import FinnishRenderer

    for case in (
        "nominative",
        "genitive",
        "accusative",
        "partitive",
        "inessive",
        "elative",
        "illative",
        "adessive",
        "ablative",
        "allative",
        "essive",
        "translative",
        "instructive",
        "abessive",
        "comitative",
    ):
        assert FinnishRenderer._inflect("sata", case, False)
        assert FinnishRenderer._inflect("sata", case, True)


def test_public_request_and_registry_error_paths():
    request = NumeralRequest(1, "en")
    assert render_request(request) == "one"
    with pytest.raises(Exception):
        realize(request, locale="en")
    with pytest.raises(Exception):
        realize(1)
    with pytest.raises(Exception):
        realize(1, locale="en", morphology=object(), gender="masculine")
    assert is_registered("en")
    assert not is_registered("not a locale")
    with pytest.raises(Exception):
        resolve_locale("xx")


def test_cli_and_compatibility_error_paths():
    for args in (
        ("--locale", "en"),
        ("x", "--locale", "en"),
        ("1/", "--locale", "en", "--fraction"),
        ("x", "--locale", "en", "--decimal"),
    ):
        with pytest.raises(SystemExit):
            main(list(args))
    with pytest.raises(TypeError):
        num2words(float("inf"))
    with pytest.raises(TypeError):
        num2words("not numeric")
    with pytest.raises(TypeError):
        num2words(1, precision=-1)
    with pytest.raises(TypeError):
        num2words(1, precision=True)
    with pytest.raises(Exception):
        num2words(1, unknown=True)
    with pytest.raises(Exception):
        num2words(1, currency="EUR")
    with pytest.raises(Exception):
        num2words(1, lang="en", to="unsupported")
    with pytest.raises(Exception):
        num2words(-1, lang="en", to="ordinal_num")


def test_large_and_negative_cardinal_paths():
    values = (
        -1,
        -21,
        100,
        101,
        999,
        1_000,
        10_005,
        100_000,
        1_000_000,
        1_000_001,
        1_000_000_000,
    )
    for locale in locales():
        if locale.startswith("pt") or locale in {"th", "vi"}:
            candidates = values[:4]
        else:
            candidates = values
        for value in candidates:
            if supports(locale, value=value):
                assert render(value, locale=locale)


def test_legacy_ordinal_and_spanish_paths():
    for value in (0, 1, 20, 21, 99, 100, 101, 999, 1000, 1001, 1_000_000):
        assert num2words(value, lang="es", to="ordinal") is not None
    for value in (100, 101, 1000, 1001, 1_000_000):
        assert num2words(value, lang="en", to="ordinal") is not None


def test_currency_scales_and_options():
    from numeralform import render_currency

    assert render_currency(1234.56, locale="en", currency="USD")
    assert render_currency(-1.25, locale="es", currency="EUR")
    assert render_currency(1.25, locale="en", currency="USD", cents=False)
    assert render_currency(1.234, locale="en", currency="KWD")
    assert render_currency(1, locale="ja", currency="JPY")
    assert render_currency(2, locale="en", currency="RUB")


def test_supported_forms_cover_renderer_branches():
    form_values = {
        NumeralForm.ORDINAL: (0, 1, 2, 10, 11, 20, 21, 99, 100, 101, 1000, 2024),
        NumeralForm.ORDINAL_NUMERIC: (0, 1, 2, 10, 21, 100),
        NumeralForm.YEAR: (
            0,
            1,
            10,
            99,
            100,
            101,
            999,
            1000,
            1999,
            2000,
            2001,
            2010,
            2024,
            2100,
        ),
        NumeralForm.DECIMAL: (
            DecimalNumber("0", "05"),
            DecimalNumber("12", "50", True),
        ),
        NumeralForm.FRACTION: (
            FractionNumber(1, 2),
            FractionNumber(2, 3),
            FractionNumber(-1, 4),
            FractionNumber(3, 11),
        ),
        NumeralForm.DIGITS: (DigitSequence("0042"), -42),
    }
    for locale in locales():
        for form, values in form_values.items():
            if form in {NumeralForm.ORDINAL, NumeralForm.YEAR} and locale.startswith(
                "pt"
            ):
                values = tuple(value for value in values if value < 90)
            if form is NumeralForm.ORDINAL and locale == "fi":
                values = tuple(value for value in values if value < 1000)
            if form is NumeralForm.DIGITS and locale == "fi":
                values = (DigitSequence("0042"),)
            for value in values:
                if supports(locale, form=form, value=value):
                    assert render(value, locale=locale, form=form)


def test_locale_specific_morphology_and_scale_paths():
    for value in (30, 40, 50, 60, 70, 80, 90, 100, 101, 999, 1000, 1001, 999999):
        assert render(value, locale="sv")
    for value in (1, 2, 3, 10, 11, 21, 100, 101, 1000, 1001, 1_000_000):
        for case in (
            Case.NOMINATIVE,
            Case.GENITIVE,
            Case.DATIVE,
            Case.ACCUSATIVE,
            Case.INSTRUMENTAL,
            Case.PREPOSITIONAL,
        ):
            assert render(value, locale="ru", case=case)
    for gender in (Gender.MASCULINE, Gender.FEMININE, Gender.NEUTER):
        assert render(3, locale="ru", form="ordinal", gender=gender)
    assert render(3, locale="ru", form="ordinal", gender="masculine", animacy="animate")
    assert render(21, locale="es", syntax="attributive", gender="feminine")
    assert render(200, locale="es", syntax="attributive", gender="feminine")
    assert render(1_000_001, locale="es", syntax="attributive", gender="masculine")
    assert render(-1, locale="es", form="digits")
    assert render(DecimalNumber("12", "50", True), locale="es", form="decimal")
    assert render(FractionNumber(-1, 11), locale="es", form="fraction")


def test_renderer_guard_paths():
    from numeralform.renderers.en import EnglishRenderer
    from numeralform.renderers.es import SpanishRenderer
    from numeralform.renderers.pt import PortugueseRenderer
    from numeralform.renderers.sv import SwedishRenderer

    english = EnglishRenderer()
    for method in (
        lambda: english._render_digits(object()),
        lambda: english._render_decimal(object()),
        lambda: english._render_fraction(object()),
        lambda: english._render_ordinal(-1),
        lambda: english._render_year(-1),
    ):
        with pytest.raises(Exception):
            method()
    spanish = SpanishRenderer()
    for method in (
        lambda: spanish._digits(object()),
        lambda: spanish._decimal(object()),
        lambda: spanish._ordinal(-1, NumeralRequest(0, "es")),
        lambda: spanish._fraction(object()),
    ):
        with pytest.raises(Exception):
            method()
    portuguese = PortugueseRenderer("pt")
    with pytest.raises(Exception):
        portuguese._cardinal("bad")
    swedish = SwedishRenderer()
    with pytest.raises(Exception):
        swedish._render_digits(object())


def test_additional_ordinal_morphology_paths():
    assert render(
        1, locale="es", form="ordinal", syntax="attributive", gender="feminine"
    )
    assert render(
        3, locale="es", form="ordinal", syntax="attributive", gender="masculine"
    )
    assert render(
        3, locale="es", form="ordinal", syntax="attributive", gender="feminine"
    )
    assert render(2, locale="ru", grammatical_number="plural", animacy="animate")
    assert render(
        3, locale="ru", form="ordinal", grammatical_number="plural", animacy="animate"
    )
    for value in (21, 30, 100, 101, 999, 1000, 1001, 999999):
        assert render(value, locale="sv", form="ordinal")
