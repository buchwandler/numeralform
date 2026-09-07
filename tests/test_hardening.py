from __future__ import annotations

import subprocess
import sys
import textwrap
import unittest

from numeralform import (
    DecimalNumber,
    DigitSequence,
    InvalidValueError,
    NumeralFormError,
    UnsupportedMorphologyError,
    render,
)


class StrictCapabilityRegressionTests(unittest.TestCase):
    def test_spanish_digit_gender_is_rejected(self):
        with self.assertRaises(UnsupportedMorphologyError):
            render(DigitSequence("12"), locale="es", gender="feminine")

    def test_spanish_digit_attributive_syntax_is_rejected(self):
        with self.assertRaises(UnsupportedMorphologyError):
            render(DigitSequence("12"), locale="es", syntax="attributive")

    def test_russian_digit_gender_is_rejected(self):
        with self.assertRaises(UnsupportedMorphologyError):
            render(DigitSequence("12"), locale="ru", gender="feminine")

    def test_russian_decimal_gender_is_rejected(self):
        with self.assertRaises(UnsupportedMorphologyError):
            render(DecimalNumber("1", "2"), locale="ru", gender="feminine")

    def test_english_digit_style_is_rejected(self):
        with self.assertRaises(NumeralFormError):
            render(DigitSequence("12"), locale="en", style="british-and")


class InvalidRequestRegressionTests(unittest.TestCase):
    def test_spanish_ordinal_outside_reviewed_range_is_package_error(self):
        with self.assertRaises(NumeralFormError):
            render(30, locale="es", form="ordinal")

    def test_russian_ordinal_outside_reviewed_range_is_package_error(self):
        with self.assertRaises(NumeralFormError):
            render(30, locale="ru", form="ordinal")

    def test_english_scale_overflow_is_rejected(self):
        with self.assertRaises(InvalidValueError):
            render(10**12, locale="en")


class RendererRegressionTests(unittest.TestCase):
    def test_spanish_masculine_apocopation_composes(self):
        expected = {
            1: "un",
            21: "veintiún",
            31: "treinta y un",
            101: "ciento un",
            121: "ciento veintiún",
            131: "ciento treinta y un",
            221: "doscientos veintiún",
            1001: "mil un",
            1021: "mil veintiún",
        }
        for value, text in expected.items():
            with self.subTest(value=value):
                self.assertEqual(
                    render(value, locale="es", syntax="attributive", gender="masculine"),
                    text,
                )

    def test_russian_scale_plural_categories(self):
        expected = {
            1_000: "одна тысяча",
            2_000: "две тысячи",
            4_000: "четыре тысячи",
            5_000: "пять тысяч",
            11_000: "одиннадцать тысяч",
            21_000: "двадцать одна тысяча",
            22_000: "двадцать две тысячи",
            25_000: "двадцать пять тысяч",
            1_000_000: "один миллион",
            2_000_000: "два миллиона",
            5_000_000: "пять миллионов",
            21_000_000: "двадцать один миллион",
            22_000_000: "двадцать два миллиона",
            25_000_000: "двадцать пять миллионов",
        }
        for value, text in expected.items():
            with self.subTest(value=value):
                self.assertEqual(render(value, locale="ru"), text)


class RegistryInitializationRegressionTests(unittest.TestCase):
    def test_custom_registration_does_not_suppress_builtins(self):
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
            assert locales() == ("en", "es", "ru", "xx"), locales()
            assert render(1, locale="xx") == "custom"
            """
        )
        completed = subprocess.run(
            [sys.executable, "-c", script],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.stdout, "")


class CapabilityCliTests(unittest.TestCase):
    def test_profile_details_are_deterministic(self):
        completed = subprocess.run(
            [sys.executable, "-m", "numeralform.cli", "--capabilities", "es"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn('"profiles"', completed.stdout)
        self.assertLess(
            completed.stdout.index('"form": "cardinal"'),
            completed.stdout.index('"form": "decimal"'),
        )


class CompatibilityTests(unittest.TestCase):
    def test_supported_num2words_mappings(self):
        from numeralform.compat import num2words
        self.assertEqual(num2words(42, lang="en"), "forty-two")
        self.assertEqual(num2words(42, lang="en", to="ordinal"), "forty-second")
        self.assertEqual(num2words(2024, lang="en", to="year"), "twenty twenty-four")

    def test_unknown_legacy_options_fail(self):
        from numeralform.compat import num2words
        with self.assertRaises(NumeralFormError):
            num2words(42, currency="EUR")


if __name__ == "__main__":
    unittest.main()
