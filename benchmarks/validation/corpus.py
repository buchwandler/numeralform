"""JSONL corpus IO, integrity manifests, and deterministic serialization."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Iterable
from pathlib import Path

from .model import ValidationCase
from .normalize import is_nfc


class CorpusError(ValueError):
    pass


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[ValidationCase]:
    cases: list[ValidationCase] = []
    seen: set[str] = set()
    previous = None
    with path.open(encoding="utf-8", newline="") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                case = ValidationCase.from_json(data)
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                raise CorpusError(f"{path}:{line_number}: invalid case: {exc}") from exc
            if case.id in seen:
                raise CorpusError(
                    f"{path}:{line_number}: duplicate case id {case.id!r}"
                )
            if previous is not None and case.id < previous:
                raise CorpusError(f"{path}:{line_number}: case IDs are not sorted")
            if not is_nfc(case.expected):
                raise CorpusError(f"{path}:{line_number}: expected output is not NFC")
            seen.add(case.id)
            previous = case.id
            cases.append(case)
    return cases


def load_exceptions(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CorpusError(f"invalid exceptions file: {exc}") from exc
    if not isinstance(records, list):
        raise CorpusError("exceptions file must contain a list")
    result: dict[str, dict[str, object]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("case_id"), str):
            raise CorpusError("exception records require a string case_id")
        if record["case_id"] in result:
            raise CorpusError(f"duplicate exception case ID: {record['case_id']}")
        if record.get("reviewed") is not True:
            raise CorpusError(f"exception {record['case_id']} is not reviewed")
        result[record["case_id"]] = record
    return result


def validate_exceptions(
    cases: list[ValidationCase], exceptions: dict[str, dict[str, object]]
) -> None:
    by_id = {case.id: case for case in cases}
    for case_id, record in exceptions.items():
        case = by_id.get(case_id)
        if case is None:
            raise CorpusError(f"stale exception refers to missing case: {case_id}")
        if record.get("oracle_output") != case.expected:
            raise CorpusError(f"stale exception oracle output for case: {case_id}")
        if not isinstance(record.get("expected_numeralform"), str):
            raise CorpusError(f"exception missing expected_numeralform: {case_id}")


def write_jsonl(path: Path, cases: Iterable[ValidationCase]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(cases, key=lambda item: item.id)
    payload = "".join(canonical_json(case.to_json()) + "\n" for case in ordered)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    os.replace(temporary, path)


def manifest_for(
    directory: Path, *, source: dict[str, object], config_sha256: str | None = None
) -> dict[str, object]:
    files: dict[str, dict[str, object]] = {}
    for path in sorted(directory.glob("*.jsonl")):
        cases = load_jsonl(path)
        files[path.name] = {"cases": len(cases), "sha256": file_sha256(path)}
    manifest: dict[str, object] = {
        "schema_version": 1,
        "source": source,
        "normalization": "NFC",
        "generated_by": "benchmarks/validation/generate_cldr.py",
        "files": files,
    }
    if config_sha256:
        manifest["config_sha256"] = config_sha256
    return manifest


def write_manifest(path: Path, manifest: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def verify_manifest(
    directory: Path, manifest_path: Path | None = None
) -> tuple[list[ValidationCase], dict[str, object]]:
    manifest_path = manifest_path or directory / "manifest.json"
    if not manifest_path.is_file():
        raise CorpusError(f"missing manifest: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CorpusError(f"invalid manifest: {exc}") from exc
    all_cases: list[ValidationCase] = []
    files = manifest.get("files", {})
    if not isinstance(files, dict):
        raise CorpusError("manifest files must be an object")
    for filename, metadata in sorted(files.items()):
        path = directory / filename
        if not path.is_file():
            raise CorpusError(f"manifest references missing file: {filename}")
        cases = load_jsonl(path)
        if metadata.get("cases") != len(cases) or metadata.get("sha256") != file_sha256(
            path
        ):
            raise CorpusError(f"manifest hash/count mismatch: {filename}")
        all_cases.extend(cases)
    return all_cases, manifest
