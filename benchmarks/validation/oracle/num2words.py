"""Verified loading and metadata for the pinned num2words benchmark oracle."""

from __future__ import annotations

import importlib.metadata
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

NUM2WORDS_REPOSITORY = "savoirfairelinux/num2words"
NUM2WORDS_COMMIT = "07814cb114157f582c40a00119c2e9faba8dcee2"
NUM2WORDS_VERSION = "0.5.14"
NUM2WORDS_PROFILE = "num2words-git-07814cb"
NUM2WORDS_PACKAGE = "num2words"


def verify_checkout(root: Path, expected_sha: str = NUM2WORDS_COMMIT) -> Path:
    """Verify that *root* is the expected Git checkout."""
    root = root.resolve()
    if not root.is_dir():
        raise RuntimeError(f"oracle checkout does not exist: {root}")
    try:
        actual = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"oracle checkout is not a Git repository: {root}") from exc
    if actual != expected_sha:
        raise RuntimeError(
            f"oracle checkout SHA mismatch: expected {expected_sha}, got {actual}"
        )
    module_path = root / NUM2WORDS_PACKAGE / "__init__.py"
    if not module_path.is_file() or not module_path.resolve().is_relative_to(root):
        raise RuntimeError(f"oracle module is missing from checkout: {module_path}")
    return root


def load_num2words(root: Path) -> object:
    """Load num2words only from a verified checkout."""
    root = verify_checkout(root)
    sys.path.insert(0, str(root))
    try:
        for name in list(sys.modules):
            if name == NUM2WORDS_PACKAGE or name.startswith(f"{NUM2WORDS_PACKAGE}."):
                del sys.modules[name]
        spec = importlib.util.find_spec(NUM2WORDS_PACKAGE)
        if spec is None or spec.origin is None:
            raise RuntimeError(f"unable to locate oracle package {NUM2WORDS_PACKAGE!r}")
        module_path = Path(spec.origin).resolve()
        if not module_path.is_relative_to(root):
            raise RuntimeError(
                f"oracle module is outside checkout: {module_path} (root {root})"
            )
        module = __import__(NUM2WORDS_PACKAGE, fromlist=["num2words"])
        return module.num2words
    finally:
        try:
            sys.path.remove(str(root))
        except ValueError:
            pass


def oracle_module(root: Path) -> ModuleType:
    """Load and return the verified num2words package module."""
    root = verify_checkout(root)
    sys.path.insert(0, str(root))
    try:
        for name in list(sys.modules):
            if name == NUM2WORDS_PACKAGE or name.startswith(f"{NUM2WORDS_PACKAGE}."):
                del sys.modules[name]
        spec = importlib.util.find_spec(NUM2WORDS_PACKAGE)
        if spec is None or spec.origin is None:
            raise RuntimeError(f"unable to locate oracle package {NUM2WORDS_PACKAGE!r}")
        module_path = Path(spec.origin).resolve()
        if not module_path.is_relative_to(root):
            raise RuntimeError(
                f"oracle module is outside checkout: {module_path} (root {root})"
            )
        return __import__(NUM2WORDS_PACKAGE, fromlist=["*"])
    finally:
        try:
            sys.path.remove(str(root))
        except ValueError:
            pass


def oracle_version(root: Path) -> str:
    """Read package metadata from the verified checkout."""
    root = verify_checkout(root)
    for distribution in importlib.metadata.distributions(path=[str(root)]):
        if distribution.metadata.get("Name", "").lower() == NUM2WORDS_PACKAGE:
            return distribution.version
    version_file = root / "bin" / NUM2WORDS_PACKAGE
    if version_file.is_file():
        for line in version_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("__version__ = "):
                return line.split("=", 1)[1].strip().strip("'\"")
    raise RuntimeError(
        f"unable to determine {NUM2WORDS_PACKAGE} package metadata from {root}"
    )


def normalize_locale(locale: str) -> str:
    """Normalize num2words registry keys to BCP-47-style spelling."""
    return locale.replace("_", "-")


def oracle_locales(root: Path) -> tuple[str, ...]:
    """Return locale keys exposed by the verified converter registry."""
    module = oracle_module(root)
    converters = getattr(module, "CONVERTER_CLASSES", None)
    if converters is None:
        converters = getattr(module, "CONVERTER_CLASSES", {})
    if not isinstance(converters, dict):
        raise TypeError("num2words converter registry is not a mapping")
    return tuple(sorted(normalize_locale(str(locale)) for locale in converters))


__all__ = [
    "NUM2WORDS_COMMIT",
    "NUM2WORDS_PACKAGE",
    "NUM2WORDS_PROFILE",
    "NUM2WORDS_REPOSITORY",
    "NUM2WORDS_VERSION",
    "load_num2words",
    "normalize_locale",
    "oracle_locales",
    "oracle_module",
    "oracle_version",
    "verify_checkout",
]
