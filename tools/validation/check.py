"""Offline checker for frozen validation corpora."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from numeralform import render

if __package__ in {None, ""}:  # support the documented ``python tools/...py`` form
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.validation.corpus import (
        CorpusError,
        load_exceptions,
        load_jsonl,
        validate_exceptions,
        verify_manifest,
    )
    from tools.validation.model import ValidationCase
    from tools.validation.normalize import is_nfc
    from tools.validation.report import Mismatch, format_mismatches, summarize
else:
    from .corpus import (
        CorpusError,
        load_exceptions,
        load_jsonl,
        validate_exceptions,
        verify_manifest,
    )
    from .model import ValidationCase
    from .normalize import is_nfc
    from .report import Mismatch, format_mismatches, summarize


def check_cases(
    cases: list[ValidationCase], exceptions: dict[str, dict[str, object]] | None = None
) -> tuple[list[Mismatch], int, int]:
    exceptions = exceptions or {}
    mismatches: list[Mismatch] = []
    matches = 0
    exceptions_used = 0
    for case in cases:
        request = case.request
        try:
            actual = render(
                request.value.as_python(),
                locale=request.locale,
                form=request.form,
                syntax=request.syntax,
                style=request.style,
                **request.morphology,
            )
        except Exception as exc:  # noqa: BLE001
            actual = f"<render error: {exc}>"
        if not is_nfc(actual):
            actual = f"<non-NFC: {actual!r}>"
        expected = (
            str(exceptions[case.id]["expected_numeralform"])
            if case.id in exceptions
            else case.expected
        )
        if actual == expected:
            matches += 1
            exceptions_used += case.id in exceptions
        else:
            mismatches.append(
                Mismatch(
                    case.id,
                    request.locale,
                    case.mapping,
                    request.form,
                    request.morphology,
                    str(request.value.to_json()),
                    expected,
                    actual,
                )
            )
    return mismatches, matches, exceptions_used


def _load_tree(
    corpus: Path,
) -> tuple[list[ValidationCase], int, str | None, dict[str, dict[str, object]]]:
    cases: list[ValidationCase] = []
    files = 0
    release = None
    exceptions: dict[str, dict[str, object]] = {}
    directories = {corpus}
    directories.update(path.parent for path in corpus.rglob("*.jsonl"))
    directories.update(path.parent for path in corpus.rglob("manifest.json"))
    for directory in sorted(directories):
        manifest_path = directory / "manifest.json"
        if manifest_path.is_file():
            group, manifest = verify_manifest(directory, manifest_path)
            cases.extend(group)
            files += len(manifest.get("files", {}))
            source = manifest.get("source", {})
            if isinstance(source, dict):
                release = source.get("cldr_version") or release
        else:
            for path in sorted(directory.glob("*.jsonl")):
                cases.extend(load_jsonl(path))
                files += 1
        exceptions.update(load_exceptions(directory / "exceptions.json"))
    validate_exceptions(cases, exceptions)
    return cases, files, str(release) if release else None, exceptions


def check_corpus(corpus: Path) -> int:
    try:
        cases, files, release, exceptions = _load_tree(corpus)
        mismatches, matches, exceptions_used = check_cases(cases, exceptions)
    except CorpusError as exc:
        print(f"CORPUS ERROR: {exc}")
        return 2
    if mismatches:
        print(format_mismatches(mismatches))
    print(
        summarize(
            mismatches,
            cases=len(cases),
            matches=matches,
            exceptions=exceptions_used,
            files=files,
            release=release,
        )
    )
    return 1 if mismatches else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    args = parser.parse_args(argv)
    return check_corpus(args.corpus)


if __name__ == "__main__":
    raise SystemExit(main())
