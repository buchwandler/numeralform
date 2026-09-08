from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from tools.validation.cases import deterministic_values
from tools.validation.corpus import (
    CorpusError,
    file_sha256,
    load_jsonl,
    validate_exceptions,
    verify_manifest,
    write_jsonl,
)
from tools.validation.model import (
    CompatInvocation,
    SerializedCompatValue,
    SerializedValue,
    ValidationCase,
    ValidationRequest,
)
from tools.validation.normalize import codepoint_repr, is_nfc
from tools.validation.report import Mismatch, group_mismatches

ROOT = Path(__file__).parents[1]


class ValidationModelTests(unittest.TestCase):
    def test_value_round_trips_without_precision_loss(self):
        for value in (
            SerializedValue("int", value="0042"),
            SerializedValue("digits", value="0042"),
            SerializedValue("decimal", integer="1", fraction="20", negative=False),
            SerializedValue("fraction", numerator="2", denominator="3"),
        ):
            decoded = SerializedValue.from_json(value.to_json())
            self.assertEqual(decoded.to_json(), value.to_json())

    def test_compatibility_invocation_round_trips_legacy_types(self):
        invocation = CompatInvocation(
            "num2words",
            (
                SerializedCompatValue.from_python(Decimal("1.20")),
                SerializedCompatValue.from_python("en"),
            ),
            {"to": SerializedCompatValue.from_python("cardinal")},
        )
        decoded = CompatInvocation.from_json(invocation.to_json())
        function, positional, kwargs = decoded.as_python()
        self.assertEqual(function, "num2words")
        self.assertEqual(positional, [Decimal("1.20"), "en"])
        self.assertEqual(kwargs, {"to": "cardinal"})

    def test_case_jsonl_is_sorted_and_hashed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.jsonl"
            request = ValidationRequest(
                SerializedValue("int", value="42"), "en", "cardinal", "standalone"
            )
            write_jsonl(
                path,
                [
                    ValidationCase("b", request, "forty-two"),
                    ValidationCase("a", request, "forty-two"),
                ],
            )
            cases = load_jsonl(path)
            self.assertEqual([case.id for case in cases], ["a", "b"])
            self.assertEqual(
                file_sha256(path), hashlib.sha256(path.read_bytes()).hexdigest()
            )

    def test_duplicate_and_unsorted_cases_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.jsonl"
            value = {
                "id": "b",
                "request": {
                    "value": {"kind": "int", "value": "1"},
                    "locale": "en",
                    "form": "cardinal",
                    "syntax": "standalone",
                    "morphology": {},
                },
                "expected": "one",
            }
            path.write_text(
                json.dumps(value) + "\n" + json.dumps(value) + "\n", encoding="utf-8"
            )
            with self.assertRaises(CorpusError):
                load_jsonl(path)

    def test_stale_exception_is_rejected(self):
        request = ValidationRequest(
            SerializedValue("int", value="42"), "en", "cardinal", "standalone"
        )
        case = ValidationCase("en-cardinal:int:42", request, "forty-two")
        with self.assertRaises(CorpusError):
            validate_exceptions(
                [case],
                {
                    case.id: {
                        "case_id": case.id,
                        "oracle_output": "forty two",
                        "expected_numeralform": "forty-two",
                        "reviewed": True,
                    }
                },
            )

    def test_report_groups_by_dimensions(self):
        mismatch = Mismatch(
            "case",
            "es",
            "map",
            "cardinal",
            {"gender": "masculine"},
            "21",
            "veintiuno",
            "veintiún",
        )
        groups = group_mismatches([mismatch])
        key = next(iter(groups))
        self.assertEqual(key[:4], ("es", "map", "cardinal", (("gender", "masculine"),)))
        self.assertIn("10^1", key[4])
        self.assertEqual(key[5], "lexical difference")

    def test_generation_is_seeded(self):
        self.assertEqual(
            deterministic_values(0, 9999, seed=20260907, per_magnitude=10),
            deterministic_values(0, 9999, seed=20260907, per_magnitude=10),
        )

    def test_nfc_and_codepoint_diagnostics(self):
        self.assertTrue(is_nfc("ё"))
        self.assertFalse(is_nfc("ё"))
        self.assertIn("U+0308", codepoint_repr("ё"))


class CorpusTests(unittest.TestCase):
    def test_committed_cldr_manifest_and_hashes(self):
        cases, manifest = verify_manifest(ROOT / "tests" / "validation" / "cldr")
        self.assertGreater(len(cases), 10000)
        self.assertEqual(manifest["source"]["cldr_version"], "48.2")

    def test_offline_checker(self):
        completed = subprocess.run(
            [
                sys.executable,
                "tools/validation/check.py",
                "--corpus",
                "tests/validation",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("mismatches: 0", completed.stdout)

    def test_external_compatibility_corpus_is_independent(self):
        generator = ROOT / "tools" / "validation" / "generate_num2words.py"
        tree = ast.parse(generator.read_text(encoding="utf-8"))
        imports = [
            node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
        ]
        self.assertNotIn("numeralform.compat", imports)
        cases, manifest = verify_manifest(
            ROOT / "tests" / "validation" / "compatibility"
        )
        self.assertGreater(len(cases), 0)
        self.assertEqual(manifest["source"]["package"], "num2words")
        self.assertEqual(manifest["source"]["version"], "0.5.14")

    def test_compatibility_cases_dispatch_through_adapter(self):
        from tools.validation.check import check_cases

        case = ValidationCase(
            "compat:en:cardinal:42",
            None,
            "forty-two",
            target="compat:num2words-0.5.14",
            invocation=CompatInvocation(
                "num2words",
                (SerializedCompatValue.from_python(42),),
                {
                    "lang": SerializedCompatValue.from_python("en"),
                    "to": SerializedCompatValue.from_python("cardinal"),
                },
            ),
        )
        mismatches, matches, _ = check_cases([case])
        self.assertEqual(mismatches, [])
        self.assertEqual(matches, 1)

    def test_runtime_does_not_import_icu(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; import numeralform; assert 'icu' not in sys.modules",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
