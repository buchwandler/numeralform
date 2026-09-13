from __future__ import annotations

import io
import runpy
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "check_artifact.py"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ('__version__ = "0.1.4"\n', "0.1.4"),
        ('__version__ = version = "0.1.4"\n', "0.1.4"),
        ('version = "0.1.4"\n', "0.1.4"),
    ],
)
def test_runtime_version_reader(source: str, expected: str) -> None:
    reader = runpy.run_path(str(SCRIPT))["_read_runtime_version"]
    assert reader(source) == expected


def _create_wheel(
    dist: Path,
    version: str,
    *,
    filename: str | None = None,
    runtime_version: str | None = None,
) -> None:
    filename = filename or f"numeralform-{version}-py3-none-any.whl"
    runtime_version = runtime_version or version
    with zipfile.ZipFile(dist / filename, "w") as wheel:
        wheel.writestr(
            "numeralform-0.0.0.dist-info/METADATA",
            "Metadata-Version: 2.3\n"
            "Name: numeralform\n"
            f"Version: {version}\n"
            "Summary: Typed, locale-aware number-to-words rendering\n",
        )
        wheel.writestr(
            "numeralform/_version.py",
            f'__version__ = version = "{runtime_version}"\n',
        )
        wheel.writestr("numeralform/py.typed", "")


def _create_sdist(dist: Path, version: str, *, filename: str | None = None) -> None:
    root = f"numeralform-{version}"
    filename = filename or f"numeralform-{version}.tar.gz"
    with tarfile.open(dist / filename, "w:gz") as archive:
        for name, content in (
            (f"{root}/LICENSE", "license"),
            (f"{root}/README.md", "readme"),
            (f"{root}/pyproject.toml", "[project]"),
            (f"{root}/numeralform/__init__.py", ""),
        ):
            info = tarfile.TarInfo(name)
            info.size = len(content.encode())
            archive.addfile(info, io.BytesIO(content.encode()))


def _run_checker(dist: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(dist), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_matching_expected_version_passes(tmp_path: Path) -> None:
    _create_wheel(tmp_path, "0.1.4")
    _create_sdist(tmp_path, "0.1.4")

    result = _run_checker(tmp_path, "--expected-version", "0.1.4")

    assert result.returncode == 0, result.stderr


def test_checker_without_expected_version_preserves_existing_invocation(
    tmp_path: Path,
) -> None:
    _create_wheel(tmp_path, "0.1.4")
    _create_sdist(tmp_path, "0.1.4")

    result = _run_checker(tmp_path)

    assert result.returncode == 0, result.stderr


def test_wheel_metadata_version_mismatch_fails(tmp_path: Path) -> None:
    _create_wheel(tmp_path, "0.1.4")
    _create_sdist(tmp_path, "0.1.4")

    result = _run_checker(tmp_path, "--expected-version", "0.1.3")

    assert result.returncode != 0
    assert "wheel metadata version mismatch" in result.stderr


def test_runtime_version_mismatch_fails(tmp_path: Path) -> None:
    _create_wheel(tmp_path, "0.1.4", runtime_version="0.1.3")
    _create_sdist(tmp_path, "0.1.4")

    result = _run_checker(tmp_path, "--expected-version", "0.1.4")

    assert result.returncode != 0
    assert "runtime __version__ mismatch" in result.stderr


def test_sdist_root_version_mismatch_fails(tmp_path: Path) -> None:
    _create_wheel(tmp_path, "0.1.4")
    _create_sdist(tmp_path, "0.1.3")
    (tmp_path / "numeralform-0.1.3.tar.gz").rename(
        tmp_path / "numeralform-0.1.4.tar.gz"
    )

    result = _run_checker(tmp_path, "--expected-version", "0.1.4")

    assert result.returncode != 0
    assert "sdist root mismatch" in result.stderr


@pytest.mark.parametrize(
    ("artifact", "mode"),
    [
        ("wheel", "missing"),
        ("wheel", "multiple"),
        ("sdist", "missing"),
        ("sdist", "multiple"),
    ],
)
def test_missing_or_multiple_artifacts_fail(
    tmp_path: Path, artifact: str, mode: str
) -> None:
    _create_wheel(tmp_path, "0.1.4")
    _create_sdist(tmp_path, "0.1.4")
    if artifact == "wheel":
        if mode == "missing":
            (tmp_path / "numeralform-0.1.4-py3-none-any.whl").unlink()
        else:
            _create_wheel(
                tmp_path,
                "0.1.4",
                filename="numeralform-0.1.4-py3-none-any-2.whl",
            )
    elif mode == "missing":
        (tmp_path / "numeralform-0.1.4.tar.gz").unlink()
    else:
        _create_sdist(tmp_path, "0.1.4", filename="numeralform-0.1.4-2.tar.gz")

    result = _run_checker(tmp_path)

    assert result.returncode != 0
    assert f"expected one {artifact}" in result.stderr
