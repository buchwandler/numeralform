from __future__ import annotations

import ast
from pathlib import Path

from benchmarks.validation.cases import deterministic_values

ROOT = Path(__file__).parents[2]


def test_generation_is_seeded():
    assert deterministic_values(
        0, 9999, seed=20260907, per_magnitude=10
    ) == deterministic_values(0, 9999, seed=20260907, per_magnitude=10)


def test_external_generator_does_not_import_compatibility_adapter():
    generator = ROOT / "benchmarks" / "validation" / "generate_num2words.py"
    tree = ast.parse(generator.read_text(encoding="utf-8"))
    imports = [
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    ]
    assert "numeralform.compat" not in imports
