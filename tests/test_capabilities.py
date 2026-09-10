from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

import pytest

from numeralform import (
    DigitSequence,
    NumeralForm,
    capabilities,
    known_locales,
    locales,
    supports,
)
from numeralform.errors import NumeralFormError


@pytest.mark.parametrize("locale", locales())
def test_supported_locales_have_executable_profiles(locale):
    samples = {
        NumeralForm.DECIMAL: Decimal(0),
        NumeralForm.FRACTION: Fraction(0, 1),
        NumeralForm.DIGITS: DigitSequence("0"),
    }
    caps = capabilities(locale)
    assert caps.forms
    for profile in caps.profiles:
        value = samples.get(profile.form, 0)
        syntax = next(iter(profile.syntaxes))
        assert supports(
            locale,
            form=profile.form,
            syntax=syntax,
            value=value,
        )


def test_baseline_locales_are_registered_but_not_supported():
    baseline = set(known_locales()) - set(locales())
    assert "am" in baseline
    for locale in baseline:
        assert not capabilities(locale).forms
        assert not supports(locale, form="cardinal", value=0)


def test_domains_agree_with_renderer_boundaries():
    assert supports("en", value=999_999_999_999)
    assert not supports("en", value=1_000_000_000_000)
    assert supports("es", form="ordinal", value=20)
    assert not supports("es", form="ordinal", value=21)
    assert supports("fi", value=9_999)
    assert not supports("fi", value=10_000)


def test_unsupported_rendering_is_an_explicit_error():
    from numeralform import render

    with pytest.raises(NumeralFormError):
        render(1, locale="am")
