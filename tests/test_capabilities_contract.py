from __future__ import annotations

import unittest
from decimal import Decimal
from fractions import Fraction

from numeralform import (
    DigitSequence,
    NumeralForm,
    capabilities,
    known_locales,
    locales,
    supports,
)
from numeralform.errors import NumeralFormError


class CapabilityContractTests(unittest.TestCase):
    def test_supported_locales_have_executable_profiles(self):
        samples = {
            NumeralForm.DECIMAL: Decimal(0),
            NumeralForm.FRACTION: Fraction(0, 1),
            NumeralForm.DIGITS: DigitSequence("0"),
        }
        for locale in locales():
            caps = capabilities(locale)
            self.assertTrue(caps.forms, locale)
            for profile in caps.profiles:
                value = samples.get(profile.form, 0)
                syntax = next(iter(profile.syntaxes))
                with self.subTest(locale=locale, form=profile.form):
                    self.assertTrue(
                        supports(
                            locale,
                            form=profile.form,
                            syntax=syntax,
                            value=value,
                        )
                    )

    def test_baseline_locales_are_registered_but_not_supported(self):
        baseline = set(known_locales()) - set(locales())
        self.assertIn("am", baseline)
        for locale in baseline:
            self.assertFalse(capabilities(locale).forms)
            self.assertFalse(supports(locale, form="cardinal", value=0))

    def test_domains_agree_with_renderer_boundaries(self):
        self.assertTrue(supports("en", value=999_999_999_999))
        self.assertFalse(supports("en", value=1_000_000_000_000))
        self.assertTrue(supports("es", form="ordinal", value=20))
        self.assertFalse(supports("es", form="ordinal", value=21))
        self.assertTrue(supports("fi", value=9_999))
        self.assertFalse(supports("fi", value=10_000))

    def test_unsupported_rendering_is_an_explicit_error(self):
        with self.assertRaises(NumeralFormError):
            from numeralform import render

            render(1, locale="am")


if __name__ == "__main__":
    unittest.main()
