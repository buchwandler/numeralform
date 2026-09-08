from __future__ import annotations

import inspect
import unittest

from numeralform import (
    DecimalNumber,
    LocaleFeatures,
    NumeralRequest,
    NumeralResult,
    realize,
    render,
)
from numeralform.errors import InvalidRequestError, InvalidValueError


class ApiContractTests(unittest.TestCase):
    def test_render_has_explicit_keywords(self):
        parameters = inspect.signature(render).parameters
        self.assertIn("form", parameters)
        self.assertIn("syntax", parameters)
        self.assertIn("morphology", parameters)
        self.assertNotIn("options", parameters)

    def test_locale_features_mapping_and_object_are_equivalent(self):
        self.assertEqual(
            render(1, locale="en", features={}),
            render(1, locale="en", features=LocaleFeatures()),
        )

    def test_form_inference_and_explicit_conflict(self):
        value = DecimalNumber("1", "20")
        self.assertEqual(realize(value, locale="en").form.value, "decimal")
        with self.assertRaises(InvalidValueError):
            render(value, locale="en", form="cardinal")

    def test_result_contains_effective_request_metadata(self):
        result = realize(42, locale="en-US", syntax="standalone")
        self.assertIsInstance(result, NumeralResult)
        self.assertEqual(result.requested_locale, "en-US")
        self.assertEqual(result.locale, "en")
        self.assertEqual(result.style, "default")
        self.assertEqual(result.syntax.value, "standalone")
        self.assertEqual(result.features, LocaleFeatures())

    def test_request_rejects_rendering_options(self):
        request = NumeralRequest(42, "en")
        with self.assertRaises(InvalidRequestError):
            realize(request, style="default")

    def test_unknown_keyword_is_rejected(self):
        with self.assertRaises(TypeError):
            render(1, locale="en", unknown=True)


if __name__ == "__main__":
    unittest.main()
