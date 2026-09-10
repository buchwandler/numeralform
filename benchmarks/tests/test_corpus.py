from __future__ import annotations

import hashlib
import json

import pytest

from benchmarks.validation.corpus import (
    CorpusError,
    file_sha256,
    load_jsonl,
    validate_exceptions,
    verify_manifest,
    write_jsonl,
)
from benchmarks.validation.model import (
    SerializedValue,
    ValidationCase,
    ValidationRequest,
)


def _case(case_id: str, expected: str = "one"):
    request = ValidationRequest(
        SerializedValue("int", value="1"), "en", "cardinal", "standalone"
    )
    return ValidationCase(case_id, request, expected)


def test_case_jsonl_is_sorted_and_hashed(tmp_path):
    path = tmp_path / "cases.jsonl"
    write_jsonl(path, [_case("b"), _case("a")])
    cases = load_jsonl(path)
    assert [case.id for case in cases] == ["a", "b"]
    assert file_sha256(path) == hashlib.sha256(path.read_bytes()).hexdigest()


def test_duplicate_and_unsorted_cases_fail(tmp_path):
    path = tmp_path / "bad.jsonl"
    value = {
        "id": "b",
        "request": {
            "value": {"kind": "int", "value": "1"},
            "locale": "en",
            "form": "cardinal",
            "syntax": "standalone",
            "morphology": {},
        },
        "expected": "one",
    }
    path.write_text(
        json.dumps(value) + "\n" + json.dumps(value) + "\n", encoding="utf-8"
    )
    with pytest.raises(CorpusError):
        load_jsonl(path)


def test_stale_exception_is_rejected():
    case = _case("en-cardinal:int:42", "forty-two")
    with pytest.raises(CorpusError):
        validate_exceptions(
            [case],
            {
                case.id: {
                    "case_id": case.id,
                    "oracle_output": "forty two",
                    "expected_numeralform": "forty-two",
                    "reviewed": True,
                }
            },
        )


def test_manifest_verification(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    path = corpus / "en.jsonl"
    write_jsonl(path, [_case("a")])
    manifest = {
        "schema_version": 1,
        "source": {"kind": "test"},
        "normalization": "NFC",
        "files": {"en.jsonl": {"cases": 1, "sha256": file_sha256(path)}},
    }
    (corpus / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    cases, loaded = verify_manifest(corpus)
    assert len(cases) == 1
    assert loaded == manifest
