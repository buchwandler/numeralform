"""Run explicit Numeralform compatibility and CLDR benchmarks."""

from __future__ import annotations

import argparse
from pathlib import Path

from .download import download_num2words
from .validation.check import _load_tree, check_cases
from .validation.corpus import CorpusError
from .validation.generate_cldr import CONFIG_PATH as CLDR_CONFIG
from .validation.generate_cldr import generate as generate_cldr
from .validation.generate_num2words import CONFIG_PATH as NUM2WORDS_CONFIG
from .validation.generate_num2words import generate as generate_num2words
from .validation.report import format_mismatches, summarize

BENCHMARK_ROOT = Path(__file__).resolve().parent
DATA_ROOT = BENCHMARK_ROOT / "data"
CORPORA_ROOT = DATA_ROOT / "corpora"
RESULTS_ROOT = DATA_ROOT / "results"
CLDR_CORPUS = CORPORA_ROOT / "cldr"
NUM2WORDS_CORPUS = CORPORA_ROOT / "num2words"


def _write_report(
    name: str,
    *,
    cases: list,
    files: int,
    release: str | None,
    exceptions: dict,
) -> int:
    mismatches, matches, exceptions_used = check_cases(cases, exceptions)
    report = []
    if mismatches:
        report.append(format_mismatches(mismatches))
        report.append("")
    report.append(
        summarize(
            mismatches,
            cases=len(cases),
            matches=matches,
            exceptions=exceptions_used,
            files=files,
            release=release,
        )
    )
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    (RESULTS_ROOT / f"{name}.txt").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    return 1 if mismatches else 0


def run_num2words() -> int:
    oracle = download_num2words()
    output = NUM2WORDS_CORPUS / "num2words-git-07814cb.jsonl"
    generate_num2words(
        output,
        config_path=NUM2WORDS_CONFIG,
        oracle_root=oracle,
    )
    cases, files, release, exceptions = _load_tree(NUM2WORDS_CORPUS)
    return _write_report(
        "num2words", cases=cases, files=files, release=release, exceptions=exceptions
    )


def run_num2words_random() -> int:
    from .randomized.generator import load_config
    from .randomized.run import DEFAULT_ORACLE_ROOT, DEFAULT_OUTPUT_DIR, run_benchmark

    config = load_config()
    randomized = config.randomized
    return run_benchmark(
        cases=int(randomized["default_cases"]),
        seed=int(randomized["default_seed"]),
        profile=str(randomized["default_profile"]),
        oracle_root=DEFAULT_ORACLE_ROOT,
        output_dir=DEFAULT_OUTPUT_DIR,
    )


def run_cldr(selected: set[str] | None = None) -> int:
    generate_cldr(CLDR_CONFIG, CLDR_CORPUS, selected)
    cases, files, release, exceptions = _load_tree(CLDR_CORPUS)
    return _write_report(
        "cldr", cases=cases, files=files, release=release, exceptions=exceptions
    )


def run(target: str, selected: set[str] | None = None) -> int:
    if target == "num2words-random":
        return run_num2words_random()
    if target == "num2words":
        return run_num2words()
    if target == "cldr":
        return run_cldr(selected)
    if target == "all":
        num2words_status = run_num2words()
        cldr_status = run_cldr(selected)
        return max(num2words_status, cldr_status)
    raise ValueError(f"unknown benchmark target: {target}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target", choices=("num2words", "num2words-random", "cldr", "all")
    )
    args = parser.parse_args(argv)
    try:
        return run(args.target)
    except (CorpusError, RuntimeError, OSError) as exc:
        print(f"BENCHMARK ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
