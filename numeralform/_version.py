"""Dynamic version derived from git metadata when available."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess


def _git_version() -> str:
    root = Path(__file__).resolve().parent.parent
    try:
        raw = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "0+unknown"

    dirty = raw.endswith("-dirty")
    if dirty:
        raw = raw[:-6]
    match = re.fullmatch(r"v?(\d+\.\d+\.\d+)(?:-(\d+)-g([0-9a-f]+))?", raw)
    if match:
        release, distance, commit = match.groups()
        if distance is None:
            version = release
        else:
            version = f"{release}.dev{distance}+g{commit}"
    else:
        version = f"0+g{raw.lstrip('v')}"
    return (
        f"{version}.dirty"
        if dirty and "+" not in version
        else f"{version}.dirty"
        if dirty
        else version
    )


__version__ = _git_version()
