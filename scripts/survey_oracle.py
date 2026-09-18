"""Survey pinned-oracle vs Numeralform output for structured value grids."""

from __future__ import annotations

import argparse
import signal
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "benchmarks/data/oracles/num2words"))

from num2words import num2words as _oracle_fn

from numeralform import render
from numeralform.model import DecimalNumber


class _OracleTimeout(Exception):
    pass


def _oracle(value, **kwargs):
    """Call the pinned oracle with a hard timeout; some locales loop forever."""

    def _handler(signum, frame):
        raise _OracleTimeout

    previous = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, 3.0)
    try:
        return _oracle_fn(value, **kwargs)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


CARDINAL_GRID = [
    0,
    1,
    2,
    3,
    10,
    11,
    14,
    19,
    20,
    21,
    42,
    55,
    69,
    74,
    88,
    99,
    100,
    101,
    111,
    155,
    200,
    205,
    300,
    472,
    500,
    701,
    999,
    1000,
    1001,
    1005,
    1010,
    1100,
    1144,
    2000,
    2345,
    3001,
    4400,
    5000,
    5043,
    8100,
    9999,
    10000,
    10001,
    11000,
    15001,
    21000,
    99876,
    100000,
    100001,
    123456,
    200000,
    456789,
    1000000,
    1000001,
    2000000,
    3000000,
    5000000,
    7000000,
    11000000,
    23000000,
    451278482,
    999999999,
]
YEAR_GRID = [
    101,
    301,
    555,
    800,
    901,
    1000,
    1001,
    1099,
    1100,
    1437,
    1635,
    1800,
    1899,
    1900,
    1901,
    1999,
    2000,
    2001,
    2020,
    2100,
    2345,
    3010,
    3873,
    6731,
    7384,
    8501,
    9499,
    9999,
]
DECIMAL_GRID = [
    "0.5",
    "0.75",
    "1.1",
    "1.5",
    "2.05",
    "3.25",
    "10.01",
    "10.10",
    "12.5",
    "20.20",
    "100.001",
    "101.01",
    "1234.5",
    "2000.25",
]

KIND_TO_NUM2WORDS = {
    "cardinal": "cardinal",
    "year": "year",
    "ordinal": "ordinal",
}


def survey(locale: str, kind: str, values, only_diff: bool) -> None:
    print(f"### {locale} / {kind}")
    same = 0
    for value in values:
        try:
            expected = _oracle(
                value, lang=locale.replace("-", "_"), to=KIND_TO_NUM2WORDS[kind]
            )
        except Exception as exc:  # noqa: BLE001
            expected = f"<ERR {type(exc).__name__}>"
        try:
            if kind == "decimal":
                text = value
                negative = text.startswith("-")
                integer, _, fraction = text.lstrip("-").partition(".")
                actual = render(
                    DecimalNumber(integer, fraction, negative),
                    locale=locale,
                    form="decimal",
                )
            else:
                actual = render(value, locale=locale, form=kind)
        except Exception as exc:  # noqa: BLE001
            actual = f"<ERR {type(exc).__name__}: {exc}>"
        mark = "  " if expected == actual else "!="
        if expected == actual:
            same += 1
            if only_diff:
                continue
        print(f"{mark} {value!r:>14} oracle={expected!r}", flush=True)
        if expected != actual:
            print(f"   {'':>14} nf    ={actual!r}", flush=True)
    print(f"[{locale}/{kind}] identical: {same}/{len(list(values))}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("locales", nargs="+")
    parser.add_argument(
        "--kind", default="cardinal", choices=["cardinal", "year", "decimal"]
    )
    parser.add_argument("--only-diff", action="store_true")
    parser.add_argument("--values", default=None, help="comma-separated custom values")
    args = parser.parse_args()
    grid = {
        "cardinal": CARDINAL_GRID,
        "year": YEAR_GRID,
        "decimal": DECIMAL_GRID,
    }[args.kind]
    if args.values:
        grid = (
            [int(v) for v in args.values.split(",")]
            if args.kind != "decimal"
            else args.values.split(",")
        )
    for locale in args.locales:
        survey(locale, args.kind, grid, args.only_diff)
    return 0


if __name__ == "__main__":
    sys.exit(main())
