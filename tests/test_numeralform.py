from __future__ import annotations

import subprocess
import sys
import unittest
from decimal import Decimal
from fractions import Fraction

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
)


class ApiTests(unittest.TestCase):
    def test_exports_and_request_result(self):
        request = NumeralRequest(
            21,
            "es-MX",
            syntax=Syntax.ATTRIBUTIVE,
            morphology=Morphology(gender=Gender.MASCULINE),
        )
        result = realize(request)
        self.assertEqual(result.text, "veintiún")
        self.assertEqual(result.locale, "es")
        self.assertEqual(result.requested_locale, "es-MX")
        self.assertEqual(result.form, NumeralForm.CARDINAL)

    def test_primitive_convenience_inputs(self):
        self.assertEqual(render(Decimal("1.20"), locale="en"), "one point two zero")
        self.assertEqual(render(Fraction(1, 2), locale="en"), "one half")

    def test_locale_normalization_and_fallback(self):
        self.assertEqual(canonicalize_locale("EN_us"), "en-US")
        self.assertEqual(canonicalize_locale("cn"), "zh-CN")
        self.assertEqual(fallback_chain("en-US"), ("en-US", "en"))
        self.assertEqual(resolve_locale("en-US"), "en")
        self.assertIn("en", locales())
        self.assertIn("ru", locales())
        self.assertNotIn("am", locales())
        self.assertIn("am", __import__("numeralform").known_locales())

    def test_capabilities_are_truthful(self):
        self.assertIn(NumeralForm.ORDINAL, capabilities("ru").forms)
        self.assertIn(Gender.FEMININE, capabilities("ru").genders)
        self.assertIn(Case.GENITIVE, capabilities("ru").cases)


class ContractTests(unittest.TestCase):
    def test_english_baseline(self):
        expected = {
            0: "zero",
            1: "one",
            2: "two",
            10: "ten",
            11: "eleven",
            19: "nineteen",
            20: "twenty",
            21: "twenty-one",
            42: "forty-two",
            99: "ninety-nine",
            100: "one hundred",
            101: "one hundred one",
            115: "one hundred fifteen",
            199: "one hundred ninety-nine",
            200: "two hundred",
            999: "nine hundred ninety-nine",
            1000: "one thousand",
            1001: "one thousand one",
            2024: "two thousand twenty-four",
            1_000_000: "one million",
            -42: "minus forty-two",
        }
        for value, text in expected.items():
            with self.subTest(value=value):
                self.assertEqual(render(value, locale="en"), text)

    def test_spanish_baseline_and_morphology(self):
        self.assertEqual(render(42, locale="es"), "cuarenta y dos")
        self.assertEqual(render(100, locale="es"), "cien")
        self.assertEqual(render(101, locale="es"), "ciento uno")
        self.assertEqual(render(1000, locale="es"), "mil")
        self.assertEqual(render(21, locale="es"), "veintiuno")
        self.assertEqual(
            render(21, locale="es", syntax="attributive", gender="masculine"),
            "veintiún",
        )
        self.assertEqual(
            render(21, locale="es", syntax="attributive", gender="feminine"),
            "veintiuna",
        )
        self.assertEqual(
            render(31, locale="es", syntax="attributive", gender="masculine"),
            "treinta y un",
        )
        self.assertEqual(
            render(1, locale="es", syntax="attributive", gender="feminine"), "una"
        )

    def test_russian_gender(self):
        self.assertEqual(render(1, locale="ru"), "один")
        self.assertEqual(render(1, locale="ru", gender="feminine"), "одна")
        self.assertEqual(render(1, locale="ru", gender="neuter"), "одно")
        self.assertEqual(render(2, locale="ru", gender="feminine"), "две")
        self.assertEqual(render(21, locale="ru", gender="feminine"), "двадцать одна")
        self.assertEqual(render(22, locale="ru", gender="feminine"), "двадцать две")
        self.assertEqual(render(1000, locale="ru"), "одна тысяча")

    def test_digits_and_precision(self):
        self.assertEqual(
            render(DigitSequence("0042"), locale="en"), "zero zero four two"
        )
        self.assertEqual(
            render(DigitSequence("0042"), locale="es"), "cero cero cuatro dos"
        )
        self.assertEqual(
            render(DecimalNumber("1", "200"), locale="en"), "one point two zero zero"
        )
        self.assertEqual(
            render(DecimalNumber("1", "20", True), locale="ru"),
            "минус один точка два ноль",
        )

    def test_forms(self):
        self.assertEqual(render(42, locale="en", form="ordinal"), "forty-second")
        self.assertEqual(render(42, locale="en", form="year"), "forty-two")
        self.assertEqual(render(FractionNumber(2, 3), locale="en"), "two thirds")
        self.assertEqual(
            render(105, locale="en", style="british-and"), "one hundred and five"
        )

    def test_unsupported_morphology_is_strict(self):
        with self.assertRaises(UnsupportedMorphologyError):
            render(2, locale="en", case="genitive")
        self.assertEqual(render(2, locale="ru", case="genitive"), "двух")
        with self.assertRaises(UnsupportedMorphologyError):
            render(2, locale="es", gender="neuter")


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "numeralform.cli", *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def test_render_command(self):
        self.assertEqual(
            self.run_cli(
                "21",
                "--locale",
                "es",
                "--syntax",
                "attributive",
                "--gender",
                "masculine",
            ),
            "veintiún",
        )
        self.assertEqual(
            self.run_cli("0042", "--locale", "en", "--digits"), "zero zero four two"
        )

    def test_discovery_commands(self):
        self.assertEqual(self.run_cli("--list-locales"), "\n".join(locales()))
        self.assertIn('"feminine"', self.run_cli("--capabilities", "ru"))


if __name__ == "__main__":
    unittest.main()
