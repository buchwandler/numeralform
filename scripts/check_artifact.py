from __future__ import annotations

import argparse
import ast
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path


def _read_runtime_version(source: str) -> str | None:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue

        names = {target.id for target in node.targets if isinstance(target, ast.Name)}
        if not {"__version__", "version"} & names:
            continue

        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return node.value.value

    return None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate built Numeralform artifacts."
    )
    parser.add_argument(
        "dist",
        nargs="?",
        default="dist",
        type=Path,
    )
    parser.add_argument(
        "--expected-version",
        help="Require wheel/sdist/runtime metadata to match this release version.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    dist: Path = args.dist
    expected_version: str | None = args.expected_version

    wheels = sorted(dist.glob("*.whl"))
    sdists = sorted(dist.glob("*.tar.gz"))
    assert len(wheels) == 1, f"expected one wheel, found {wheels}"
    assert len(sdists) == 1, f"expected one sdist, found {sdists}"

    with zipfile.ZipFile(wheels[0]) as wheel:
        names = set(wheel.namelist())
        metadata_name = next(
            name for name in names if name.endswith(".dist-info/METADATA")
        )
        metadata_text = wheel.read(metadata_name).decode()
        metadata = Parser().parsestr(metadata_text)

        assert metadata["Name"] == "numeralform"
        assert "Typed, locale-aware number-to-words" in (metadata["Summary"] or "")
        assert any(name.endswith("numeralform/py.typed") for name in names)
        assert not any(name.startswith("benchmarks/") for name in names)
        assert not any(name.startswith(".ledger/") for name in names)

        if expected_version is not None:
            actual_version = metadata["Version"]
            assert actual_version == expected_version, (
                "wheel metadata version mismatch: "
                f"expected {expected_version}, got {actual_version}"
            )

            version_source = wheel.read("numeralform/_version.py").decode()
            runtime_version = _read_runtime_version(version_source)
            assert runtime_version is not None, (
                "unable to read numeralform/_version.py version"
            )
            assert runtime_version == expected_version, (
                "runtime __version__ mismatch: "
                f"expected {expected_version}, got {runtime_version}"
            )

    with tarfile.open(sdists[0]) as sdist:
        names = set(sdist.getnames())

        assert any(name.endswith("/LICENSE") for name in names)
        assert any(name.endswith("/README.md") for name in names)
        assert any(name.endswith("/pyproject.toml") for name in names)
        assert any("/numeralform/__init__.py" in name for name in names)

        if expected_version is not None:
            expected_root = f"numeralform-{expected_version}"
            roots = {name.split("/", 1)[0] for name in names if name}
            assert roots == {expected_root}, (
                f"sdist root mismatch: expected {expected_root}, got {sorted(roots)}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
