"""Optional secondary num2words2 benchmark helpers."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import tomllib

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "num2words2.toml"


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def verify_checkout(root: Path, config_path: Path = CONFIG_PATH) -> Path:
    root = root.resolve()
    expected = load_config(config_path)["oracle"]["commit"]
    actual = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != expected:
        raise RuntimeError(
            f"num2words2 checkout SHA mismatch: expected {expected}, got {actual}"
        )
    return root


def compare_overlap(
    cases: list[tuple[object, dict[str, Any]]],
    oracle: Callable[..., Any],
    secondary: Callable[..., Any],
) -> dict[str, int]:
    counts = {"match": 0, "mismatch": 0}
    for value, kwargs in cases:
        if oracle(value, **kwargs) == secondary(value, **kwargs):
            counts["match"] += 1
        else:
            counts["mismatch"] += 1
    return counts


__all__ = ["CONFIG_PATH", "compare_overlap", "load_config", "verify_checkout"]
