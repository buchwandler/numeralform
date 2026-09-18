"""Replay stored randomized differences against the current Numeralform build.

Loads the JSONL difference records produced by a benchmark run, re-renders each
case through the canonical adapters, compares against the recorded oracle text
with the current equivalence rules, and reports residual mismatch groups with
representative examples.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from benchmarks.randomized.adapters import run_numeralform_canonical
from benchmarks.randomized.compare import compare_results
from benchmarks.randomized.model import RandomCase, SerializedRandomValue


def load_cases(path: Path) -> list[tuple[RandomCase, str, str]]:
    cases: list[tuple[RandomCase, str, str]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            payload = row["case"]
            case = RandomCase(
                schema_version=payload["schema_version"],
                generator_version=payload["generator_version"],
                seed=payload["seed"],
                index=payload["index"],
                case_id=payload["case_id"],
                locale=payload["locale"],
                kind=payload["kind"],
                surface=payload["surface"],
                value=SerializedRandomValue.from_dict(payload["value"]),
                currency=payload.get("currency"),
                tags=tuple(payload.get("tags", ())),
                oracle_locale=payload.get("oracle_locale"),
                options=payload.get("options", {}),
                variant_id=payload.get("variant_id"),
                call_variant=payload.get("call_variant"),
                transport=payload.get("transport", "native"),
            )
            oracle_text = row["num2words"]["text"] or ""
            cases.append((case, oracle_text, row.get("difference_shape", "")))
    return cases


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        nargs="?",
        default=str(
            REPO_ROOT / "benchmarks/data/results/num2words-random/differences.jsonl"
        ),
    )
    parser.add_argument("--locale", default=None)
    parser.add_argument("--kind", default=None)
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--show-variants", action="store_true")
    args = parser.parse_args()

    cases = load_cases(Path(args.path))
    groups: dict[tuple[str, str, str], list] = defaultdict(list)
    statuses: dict[str, int] = defaultdict(int)
    rules: dict[str, int] = defaultdict(int)
    for case, oracle_text, shape in cases:
        if args.locale and case.locale != args.locale:
            continue
        if args.kind and case.kind != args.kind:
            continue
        actual = run_numeralform_canonical(case)
        result = compare_results(
            case,
            _text_result(oracle_text),
            actual,
            accept_variants=True,
        )
        statuses[result.status] += 1
        if result.status == "variant":
            rules[result.equivalence_rule or "?"] += 1
            if not args.show_variants:
                continue
        if result.status != "match":
            groups[(case.locale, case.kind, result.status)].append(
                (
                    case.surface,
                    oracle_text,
                    actual.text
                    if actual.outcome == "text"
                    else f"<{actual.exception_type}>",
                    result.equivalence_rule,
                )
            )

    print("statuses:", dict(sorted(statuses.items())))
    if rules:
        print("variant rules:", dict(sorted(rules.items())))
    for key in sorted(groups, key=lambda k: -len(groups[k])):
        examples = groups[key][: args.limit]
        print(f"\n== {key[0]} / {key[1]} / {key[2]}: {len(groups[key])} ==")
        for surface, oracle, actual, rule in examples:
            print(f"  {surface}: oracle={oracle!r}")
            print(f"           nf    ={actual!r} rule={rule}")
    return 0


def _text_result(text: str):
    from benchmarks.randomized.model import ExecutionResult

    return ExecutionResult.text_result(text)


if __name__ == "__main__":
    sys.exit(main())
