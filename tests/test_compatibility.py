from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from decimal import Decimal

import pytest

from numeralform import render, render_currency
from numeralform.compat import num2words


def _run(extra_path=None):
    script = "from numeralform.compat import num2words; print(num2words(42, lang='en'))"
    env = os.environ.copy()
    if extra_path:
        env["PYTHONPATH"] = extra_path + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip()


def test_fake_upstream_cannot_change_output(tmp_path):
    package = tmp_path / "num2words"
    package.mkdir()
    (package / "__init__.py").write_text(
        "def num2words(*args, **kwargs): return 'BROKEN ORACLE'\n",
        encoding="utf-8",
    )
    assert _run(str(tmp_path)) == "forty-two"


def test_upstream_unavailable_does_not_break_adapter():
    script = textwrap.dedent(
        """
        import sys
        sys.modules['num2words'] = None
        from numeralform.compat import num2words
        assert num2words(42, lang='en') == 'forty-two'
        """
    )
    subprocess.run([sys.executable, "-c", script], check=True)


def test_integer_currency_input_is_minor_units_only_in_compatibility_mode():
    canonical = render_currency(5, locale="en", currency="EUR")
    legacy = num2words(5, lang="en", to="currency", currency="EUR")
    assert "five euros" in canonical
    assert "zero euro" in legacy
    assert "five cents" in legacy


def test_rounding_and_cents_false():
    assert "three euro" in num2words(Decimal("2.995"), lang="en", to="currency")
    assert ", 05 cents" in num2words(5, lang="en", to="currency", cents=False)


def test_variable_currency_scale():

    assert (
        num2words(5, lang="en", to="currency", currency="JPY") == "zero yen, five sen"
    )
    assert "fils" in num2words(
        Decimal("1.001"), lang="en", to="currency", currency="KWD"
    )


def test_german_currency_matches_pinned_num2words_morphology():
    assert (
        num2words(
            Decimal("301.58"),
            lang="de",
            to="currency",
            currency="EUR",
        )
        == "dreihundertein Euro und achtundfünfzig Cent"
    )

    assert (
        num2words(
            Decimal("4216.01"),
            lang="de",
            to="currency",
            currency="GBP",
        )
        == "viertausendzweihundertsechzehn Pfund und ein Penny"
    )


def test_legacy_jpy_decimal_marker_controls_zero_sen_output():
    assert (
        num2words(Decimal(61), lang="en", to="currency", currency="JPY")
        == "sixty-one yen"
    )
    assert (
        num2words(Decimal("61.0"), lang="en", to="currency", currency="JPY")
        == "sixty-one yen, zero sen"
    )
    assert (
        num2words(Decimal("61.50"), lang="en", to="currency", currency="JPY")
        == "sixty-one yen, fifty sen"
    )


def test_english_regional_canonical_dialects_do_not_change_compatibility():
    assert num2words(582378.922, lang="en", to="cardinal") == (
        "five hundred and eighty-two thousand, three hundred and seventy-eight point nine two two"
    )
    assert num2words(53184, lang="en", to="currency", currency="USD") == (
        "five hundred and thirty-one dollars, eighty-four cents"
    )
    assert num2words(92811, lang="en", to="currency", currency="GBP") == (
        "nine hundred and twenty-eight pounds sterling, eleven pence"
    )


def test_indian_english_uses_lakh_and_crore():
    assert render(100_000, locale="en-IN") == "one lakh"
    assert render(10_000_000, locale="en-IN") == "one crore"
    assert num2words(100_000, lang="en-IN") == "one lakh"


def test_belgian_and_swiss_french_have_regional_tens():
    assert render(70, locale="fr-BE") == "septante"
    assert render(90, locale="fr-BE") == "nonante"
    assert render(70, locale="fr-CH") == "septante"
    assert render(80, locale="fr-CH") == "huitante"
    assert render(90, locale="fr-CH") == "nonante"


def test_float_decimal_and_scientific_string_inputs():
    assert "point" in num2words(123.4, lang="en")
    assert "point" in num2words(Decimal("1.20"), lang="de")
    assert "thousand" in num2words("1e3", lang="en")


@pytest.mark.parametrize(
    "locale",
    (
        "cs",
        "de",
        "en",
        "en-IN",
        "en-NG",
        "es",
        "es-CO",
        "es-CR",
        "es-GT",
        "es-NI",
        "es-VE",
        "fi",
        "fr",
        "fr-BE",
        "fr-CH",
        "fr-DZ",
        "it",
        "ja",
        "ko",
        "pt",
        "pt-BR",
        "pt-PT",
        "ru",
        "sv",
        "th",
        "vi",
    ),
)
def test_decimal_fallback_covers_all_current_real_locales(locale):
    assert num2words(12.5, lang=locale)


def test_underscore_and_hyphen_are_not_collapsed():
    from numeralform.compat._num2words.registry import resolve_compat_locale

    assert resolve_compat_locale("en_IN").resolution.upstream_key == "en_IN"
    assert resolve_compat_locale("en-IN").resolution.upstream_key == "en"
    assert resolve_compat_locale("fr-CH").resolution.numeralform_locale == "fr"


def test_true_uses_legacy_numeric_behavior():
    assert num2words(True, lang="en") == num2words(1, lang="en")


def test_year_1000_in_chinese():
    assert num2words(1000, lang="zh", to="year") == "一零零零年"


def test_year_2024_in_chinese():
    assert num2words(2024, lang="zh", to="year") == "二零二四年"


def test_hyphenated_regional_tags_use_legacy_fallback():
    assert num2words(2024, lang="zh-CN", to="year") == num2words(
        2024, lang="zh", to="year"
    )


def test_fraction_string_and_precision():
    assert "one third" in num2words("1/3", lang="en")
    assert "one third" in num2words("1/3", lang="en", to="fraction")
    assert "point" in num2words(1.239, lang="en", precision=2)


def test_pinned_compatibility_regression_fixtures():
    assert num2words(690173780, lang="en") == (
        "six hundred and ninety million, one hundred and seventy-three thousand, "
        "seven hundred and eighty"
    )
    assert num2words(Decimal("1.20"), lang="es") == "uno punto dos"
    assert num2words(Decimal("1.20"), lang="ru") == "одна целая двадцать сотых"
    assert num2words(2024, lang="ja", to="year") == "令和六年"
    assert num2words(1901, lang="en", to="year") == "nineteen oh-one"
    assert num2words(100001, lang="pt") == "cem mil e um"
    assert num2words(83, lang="fr-BE", to="ordinal") == "quatre-vingt-troisième"
