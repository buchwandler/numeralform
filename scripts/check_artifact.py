from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path


def main() -> int:
    dist = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    wheels = sorted(dist.glob("*.whl"))
    sdists = sorted(dist.glob("*.tar.gz"))
    assert len(wheels) == 1, f"expected one wheel, found {wheels}"
    assert len(sdists) == 1, f"expected one sdist, found {sdists}"

    with zipfile.ZipFile(wheels[0]) as wheel:
        names = set(wheel.namelist())
        metadata_name = next(
            name for name in names if name.endswith(".dist-info/METADATA")
        )
        metadata = wheel.read(metadata_name).decode()
        assert "Summary: Typed, locale-aware number-to-words" in metadata
        assert any(name.endswith("numeralform/py.typed") for name in names)
        assert not any(name.startswith("benchmarks/") for name in names)
        assert not any(name.startswith(".ledger/") for name in names)

    with tarfile.open(sdists[0]) as sdist:
        names = set(sdist.getnames())
        assert any(name.endswith("/LICENSE") for name in names)
        assert any(name.endswith("/README.md") for name in names)
        assert any(name.endswith("/pyproject.toml") for name in names)
        assert any("/numeralform/__init__.py" in name for name in names)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
