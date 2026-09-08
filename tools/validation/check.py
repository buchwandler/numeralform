"""Offline checker for frozen validation corpora."""

from __future__ import annotations

# ruff: noqa: I001
import argparse
import re
import sys
from pathlib import Path


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

from numeralform import render


def _exception_matches(
    exc: Exception, expected_type: str, message_pattern: str | None
) -> bool:
    names = {type(exc).__name__, f"{type(exc).__module__}.{type(exc).__name__}"}
    if expected_type not in names:
        return False
    return message_pattern is None or re.search(message_pattern, str(exc)) is not None


def _compatibility_call(case: ValidationCase) -> tuple[str | None, Exception | None]:
    if case.invocation is not None:
        function, positional, kwargs = case.invocation.as_python()
    elif case.request is not None:
        request = case.request
        if request.form == "currency":
            function = "num2words"
            positional = [request.value.as_python()]
            kwargs = {"lang": request.locale, "to": request.form}
        else:
            function = "num2words"
            positional = [request.value.as_python()]
            kwargs = {"lang": request.locale, "to": request.form}
    else:  # pragma: no cover - ValidationCase rejects this state.
        raise ValueError("compatibility case has no invocation")
    if function not in {"num2words", "numeralform.compat.num2words"}:
        raise ValueError(f"unsupported compatibility function: {function!r}")
    try:
        from numeralform.compat import num2words as compat_num2words

        return str(compat_num2words(*positional, **kwargs)), None
    except Exception as exc:  # noqa: BLE001
        return None, exc


def check_cases(
    cases: list[ValidationCase], exceptions: dict[str, dict[str, object]] | None = None
) -> tuple[list[Mismatch], int, int]:
    exceptions = exceptions or {}
    mismatches: list[Mismatch] = []
    matches = 0
    exceptions_used = 0
    for case in cases:
        if case.target == "compat:num2words-0.5.14":
            actual_result, actual_exception = _compatibility_call(case)
            expected = case.expected
            if case.expected_exception_type is not None:
                matched = actual_exception is not None and _exception_matches(
                    actual_exception,
                    case.expected_exception_type,
                    case.expected_exception_message_pattern,
                )
                actual = (
                    f"<exception {type(actual_exception).__name__}: {actual_exception}>"
                    if actual_exception is not None
                    else str(actual_result)
                )
            else:
                actual = (
                    f"<exception {type(actual_exception).__name__}: {actual_exception}>"
                    if actual_exception is not None
                    else actual_result
                )
                matched = actual_exception is None and actual == expected
        else:
            request = case.request
            if request is None:
                raise ValueError("canonical validation case requires a request")
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
            matched = actual == expected
            exceptions_used += matched and case.id in exceptions
        if matched:
            matches += 1
            continue
        request = case.request
        locale = request.locale if request is not None else "<compat>"
        form = request.form if request is not None else "compatibility"
        morphology = request.morphology if request is not None else {}
        value = (
            str(request.value.to_json())
            if request is not None
            else str(case.invocation.to_json() if case.invocation else "")
        )
        mismatches.append(
            Mismatch(
                case.id,
                locale,
                case.mapping,
                form,
                morphology,
                value,
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
    if not cases:
        raise CorpusError(f"validation corpus contains no cases: {corpus}")
    validate_exceptions(cases, exceptions)
    return cases, files, str(release) if release else None, exceptions


def check_corpus(corpus: Path) -> int:
    try:
        if not corpus.is_dir():
            raise CorpusError(f"validation corpus directory is missing: {corpus}")
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
