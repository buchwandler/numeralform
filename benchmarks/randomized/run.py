"""Run the randomized num2words differential benchmark."""

from __future__ import annotations

import argparse
import json
import platform
import random
from collections.abc import Iterable
from pathlib import Path

import numeralform
from benchmarks.validation.oracle.num2words import (
    NUM2WORDS_COMMIT,
    NUM2WORDS_PROFILE,
    NUM2WORDS_REPOSITORY,
    NUM2WORDS_VERSION,
    load_num2words,
    oracle_locales,
    oracle_version,
)

from .adapters import run_num2words, run_numeralform
from .compare import compare_results
from .generator import CONFIG_PATH, generate_cases, load_config
from .model import DifferentialResult, RandomCase
from .report import write_reports

BENCHMARK_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ORACLE_ROOT = BENCHMARK_ROOT / "data" / "oracles" / "num2words"
DEFAULT_OUTPUT_DIR = BENCHMARK_ROOT / "data" / "results" / "num2words-random"


def execute_case(case: RandomCase, external_num2words) -> DifferentialResult:
    return compare_results(
        case,
        run_num2words(case, external_num2words),
        run_numeralform(case),
    )


def _load_replay(path: Path, case_id: str) -> RandomCase:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        case = RandomCase.from_dict(payload["case"])
        if case.case_id == case_id:
            return case
    raise ValueError(f"case ID not found in replay file: {case_id}")


def _seed(value: str) -> int:
    if value == "auto":
        return random.SystemRandom().randrange(0, 2**63)
    return int(value)


def _metadata(seed: int, profile: str, requested_cases: int, config, version: str) -> dict:
    return {
        "schema_version": 1,
        "generator_version": 1,
        "seed": seed,
        "profile": profile,
        "requested_cases": requested_cases,
        "config_hash": config.config_hash,
        "num2words": {
            "repository": NUM2WORDS_REPOSITORY,
            "commit": NUM2WORDS_COMMIT,
            "version_metadata": version,
            "profile": NUM2WORDS_PROFILE,
        },
        "numeralform_version": numeralform.__version__,
        "python_version": platform.python_version(),
    }


def run_benchmark(
    *,
    cases: int,
    seed: int,
    profile: str,
    oracle_root: Path,
    output_dir: Path,
    locales: Iterable[str] = (),
    kinds: Iterable[str] = (),
    currencies: Iterable[str] = (),
    record_all: bool = False,
    fail_on_diff: bool = False,
) -> int:
    external_num2words = load_num2words(oracle_root)
    version = oracle_version(oracle_root)
    if version != NUM2WORDS_VERSION:
        raise RuntimeError(f"unsupported oracle version {version!r}; expected {NUM2WORDS_VERSION!r}")
    config = load_config(CONFIG_PATH, profile)
    external_locales = oracle_locales(oracle_root)
    generated, generation_stats, _ = generate_cases(
        seed=seed,
        count=cases,
        profile=profile,
        locales=locales or None,
        kinds=kinds or None,
        currencies=currencies or None,
        external_locales=external_locales,
        config_path=CONFIG_PATH,
    )
    results = tuple(execute_case(case, external_num2words) for case in generated)
    metadata = _metadata(seed, profile, cases, config, version)
    paths = write_reports(
        results,
        output_dir,
        metadata=metadata,
        generation_stats=generation_stats,
        record_all=record_all,
    )
    counts = {status: sum(result.status == status for result in results) for status in ("match", "mismatch", "oracle-error", "numeralform-error", "both-error")}
    print("num2words-random benchmark")
    print(f"oracle: {NUM2WORDS_COMMIT}")
    print(f"seed: {seed}")
    print(f"profile: {profile}")
    print(f"cases: {len(results)}")
    for status, value in counts.items():
        print(f"{status + ':':20}{value}")
    print(f"report: {paths['report']}")
    print(f"differences: {paths['differences']}")
    return 1 if fail_on_diff and any(result.status != "match" for result in results) else 0


def run_replay(path: Path, case_id: str, oracle_root: Path) -> int:
    case = _load_replay(path, case_id)
    result = execute_case(case, load_num2words(oracle_root))
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if result.status != "match" else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=int, default=10000)
    parser.add_argument("--seed", default="20260910", type=_seed)
    parser.add_argument("--profile", choices=("common", "stress"), default="common")
    parser.add_argument("--locale", action="append", dest="locales", default=[])
    parser.add_argument("--kind", action="append", dest="kinds", default=[])
    parser.add_argument("--currency", action="append", dest="currencies", default=[])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--oracle-root", type=Path, default=DEFAULT_ORACLE_ROOT)
    parser.add_argument("--record-all", action="store_true")
    parser.add_argument("--fail-on-diff", action="store_true")
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--case-id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.replay is not None:
        if not args.case_id:
            raise ValueError("--case-id is required with --replay")
        return run_replay(args.replay, args.case_id, args.oracle_root)
    if args.cases < 0:
        raise ValueError("--cases must be non-negative")
    return run_benchmark(
        cases=args.cases,
        seed=args.seed,
        profile=args.profile,
        oracle_root=args.oracle_root,
        output_dir=args.output_dir,
        locales=args.locales,
        kinds=args.kinds,
        currencies=args.currencies,
        record_all=args.record_all,
        fail_on_diff=args.fail_on_diff,
    )


__all__ = ["build_parser", "execute_case", "main", "run_benchmark", "run_replay"]
