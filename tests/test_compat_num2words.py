from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from decimal import Decimal

from numeralform import render, render_currency
from numeralform.compat import num2words


class CompatibilityEnvironmentTests(unittest.TestCase):
    def _run(self, extra_path=None):
        script = (
            "from numeralform.compat import num2words; print(num2words(42, lang='en'))"
        )
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

    def test_fake_upstream_cannot_change_output(self):
        with tempfile.TemporaryDirectory() as directory:
            package = os.path.join(directory, "num2words")
            os.mkdir(package)
            with open(
                os.path.join(package, "__init__.py"), "w", encoding="utf-8"
            ) as handle:
                handle.write("def num2words(*args, **kwargs): return 'BROKEN ORACLE'\n")
            self.assertEqual(self._run(directory), "forty-two")

    def test_upstream_unavailable_does_not_break_adapter(self):
        script = textwrap.dedent(
            """
            import sys
            sys.modules['num2words'] = None
            from numeralform.compat import num2words
            assert num2words(42, lang='en') == 'forty-two'
            """
        )
        subprocess.run([sys.executable, "-c", script], check=True)


class CompatibilityCurrencyTests(unittest.TestCase):
    def test_integer_currency_input_is_minor_units_only_in_compatibility_mode(self):
        canonical = render_currency(5, locale="en", currency="EUR")
        legacy = num2words(5, lang="en", to="currency", currency="EUR")
        self.assertIn("five euros", canonical)
        self.assertIn("zero euros", legacy)
        self.assertIn("five cents", legacy)

    def test_rounding_and_cents_false(self):
        self.assertIn(
            "three euros", num2words(Decimal("2.995"), lang="en", to="currency")
        )
        self.assertIn(", 05 cents", num2words(5, lang="en", to="currency", cents=False))

    def test_variable_currency_scale(self):
        self.assertEqual(
            num2words(5, lang="en", to="currency", currency="JPY"), "five yen"
        )
        self.assertIn(
            "fils",
            num2words(Decimal("1.001"), lang="en", to="currency", currency="KWD"),
        )


class RegionalCompatibilityTests(unittest.TestCase):
    def test_indian_english_uses_lakh_and_crore(self):
        self.assertEqual(render(100_000, locale="en-IN"), "one lakh")
        self.assertEqual(render(10_000_000, locale="en-IN"), "one crore")
        self.assertIn("lakh", num2words(100_000, lang="en-IN"))

    def test_belgian_and_swiss_french_have_regional_tens(self):
        self.assertEqual(render(70, locale="fr-BE"), "septante")
        self.assertEqual(render(90, locale="fr-BE"), "nonante")
        self.assertEqual(render(70, locale="fr-CH"), "septante")
        self.assertEqual(render(80, locale="fr-CH"), "huitante")
        self.assertEqual(render(90, locale="fr-CH"), "nonante")


class DecimalCompatibilityTests(unittest.TestCase):
    def test_float_decimal_and_scientific_string_inputs(self):
        self.assertIn("point", num2words(123.4, lang="en"))
        self.assertIn("point", num2words(Decimal("1.20"), lang="de"))
        self.assertIn("thousand", num2words("1e3", lang="en"))

    def test_decimal_fallback_covers_all_current_real_locales(self):
        locales = (
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
        )
        for locale in locales:
            with self.subTest(locale=locale):
                self.assertTrue(num2words(12.5, lang=locale))


class SupersetCompatibilityTests(unittest.TestCase):
    def test_fraction_string_and_precision(self):
        self.assertIn("one third", num2words("1/3", lang="en"))
        self.assertIn("one third", num2words("1/3", lang="en", to="fraction"))
        self.assertIn("point", num2words(1.239, lang="en", precision=2))


if __name__ == "__main__":
    unittest.main()
