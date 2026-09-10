"""Exact differential comparison and explanatory difference classification."""

from __future__ import annotations

import re
import unicodedata

from .adapters import normalize
from .model import DifferentialResult, ExecutionResult, RandomCase

_PUNCTUATION_RE = re.compile(r"[^\w\s]", re.UNICODE)


def difference_shape(expected: str, actual: str) -> str:
    """Classify a textual difference without treating it as a match."""
    if expected.replace("-", " ") == actual.replace("-", " "):
        return "hyphenation only"
    if expected.split() == actual.split():
        return "whitespace only"
    if expected.casefold() == actual.casefold():
        return "case only"
    if _PUNCTUATION_RE.sub("", expected) == _PUNCTUATION_RE.sub("", actual):
        return "punctuation difference"
    if expected.startswith(actual) or actual.startswith(expected):
        return "prefix/suffix difference"
    if any(token in expected or token in actual for token in (" y ", " and ", " et ")):
        return "conjunction difference"
    if unicodedata.normalize("NFD", expected) == unicodedata.normalize("NFD", actual):
        return "Unicode normalization difference"
    return "lexical difference"


def compare_results(
    case: RandomCase,
    num2words: ExecutionResult,
    numeralform: ExecutionResult,
) -> DifferentialResult:
    """Compare two execution results and return a replayable result."""
    oracle_text = num2words.text
    canonical_text = numeralform.text
    if num2words.outcome == "text" and numeralform.outcome == "text":
        assert oracle_text is not None and canonical_text is not None
        oracle_text = normalize(oracle_text)
        canonical_text = normalize(canonical_text)
        if oracle_text == canonical_text:
            return DifferentialResult(case, "match", num2words, numeralform)
        return DifferentialResult(
            case,
            "mismatch",
            num2words,
            numeralform,
            difference_shape(oracle_text, canonical_text),
        )
    if num2words.outcome == "exception" and numeralform.outcome == "exception":
        return DifferentialResult(case, "both-error", num2words, numeralform)
    if num2words.outcome == "exception":
        return DifferentialResult(case, "oracle-error", num2words, numeralform)
    return DifferentialResult(case, "numeralform-error", num2words, numeralform)


__all__ = ["compare_results", "difference_shape"]
