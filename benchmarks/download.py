"""Acquire pinned external benchmark oracle checkouts."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

BENCHMARK_ROOT = Path(__file__).resolve().parent
DATA_ROOT = BENCHMARK_ROOT / "data"
NUM2WORDS_ROOT = DATA_ROOT / "oracles" / "num2words"
NUM2WORDS_REPOSITORY = "https://github.com/savoirfairelinux/num2words.git"
NUM2WORDS_COMMIT = "07814cb114157f582c40a00119c2e9faba8dcee2"
NUM2WORDS_MODULE = NUM2WORDS_ROOT / "num2words" / "__init__.py"


def _git_revision(path: Path) -> str:
    if not (path / ".git").exists():
        raise RuntimeError(f"oracle is not a Git checkout: {path}")
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"oracle is not a usable Git checkout: {path}") from exc


def _verify_checkout(path: Path) -> None:
    revision = _git_revision(path)
    if revision != NUM2WORDS_COMMIT:
        raise RuntimeError(
            f"oracle revision mismatch: expected {NUM2WORDS_COMMIT}, got {revision}; "
            "rerun with --replace to replace it"
        )
    module = path / "num2words" / "__init__.py"
    if not module.is_file() or not module.resolve().is_relative_to(path.resolve()):
        raise RuntimeError(f"oracle module is missing from checkout: {module}")


def download_num2words(*, replace: bool = False) -> Path:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    if NUM2WORDS_ROOT.exists():
        try:
            _verify_checkout(NUM2WORDS_ROOT)
        except RuntimeError:
            if not replace:
                raise
            shutil.rmtree(NUM2WORDS_ROOT)
        else:
            print(f"num2words oracle already verified: {NUM2WORDS_ROOT}")
            return NUM2WORDS_ROOT

    staging = Path(tempfile.mkdtemp(prefix=".num2words-", dir=DATA_ROOT))
    checkout = staging / "checkout"
    try:
        subprocess.run(
            ["git", "clone", NUM2WORDS_REPOSITORY, str(checkout)],
            check=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", str(checkout), "checkout", "--detach", NUM2WORDS_COMMIT],
            check=True,
            text=True,
        )
        _verify_checkout(checkout)
        if NUM2WORDS_ROOT.exists():
            if not replace:
                raise RuntimeError(
                    f"oracle checkout appeared during download: {NUM2WORDS_ROOT}; "
                    "rerun with --replace to replace it"
                )
            shutil.rmtree(NUM2WORDS_ROOT)
        NUM2WORDS_ROOT.parent.mkdir(parents=True, exist_ok=True)
        checkout.rename(NUM2WORDS_ROOT)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"unable to acquire pinned num2words oracle: {exc}") from exc
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    print(f"downloaded and verified num2words oracle: {NUM2WORDS_ROOT}")
    return NUM2WORDS_ROOT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=("num2words",))
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace an existing checkout only after explicit confirmation",
    )
    args = parser.parse_args(argv)
    if args.target == "num2words":
        download_num2words(replace=args.replace)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"DOWNLOAD ERROR: {exc}")
        raise SystemExit(2) from exc
