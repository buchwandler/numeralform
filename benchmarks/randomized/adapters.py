"""Implementation-specific adapters for randomized differential cases."""

from __future__ import annotations

import unicodedata
from collections.abc import Callable
from typing import Any

from numeralform import render, render_currency

from .model import ExecutionResult, RandomCase

_NUM2WORDS_FORMS = {
    "cardinal": "cardinal",
    "decimal": "cardinal",
    "ordinal": "ordinal",
    "year": "year",
}


def normalize(text: object) -> str:
    return unicodedata.normalize("NFC", str(text))


def run_num2words(case: RandomCase, external_num2words: Callable[..., Any]) -> ExecutionResult:
    """Execute a case against the supplied, already verified oracle function."""
    try:
        kwargs: dict[str, Any] = {"lang": case.locale.replace("-", "_")}
        if case.kind == "currency":
            kwargs.update(to="currency", currency=case.currency)
        else:
            kwargs["to"] = _NUM2WORDS_FORMS[case.kind]
        text = external_num2words(case.python_value(), **kwargs)
        return ExecutionResult.text_result(normalize(text))
    except Exception as exc:  # noqa: BLE001
        return ExecutionResult.exception_result(exc)


def run_numeralform(
    case: RandomCase,
    *,
    render_function: Callable[..., Any] = render,
    render_currency_function: Callable[..., Any] = render_currency,
) -> ExecutionResult:
    """Execute a case through canonical Numeralform."""
    try:
        if case.kind == "currency":
            text = render_currency_function(
                case.python_value(),
                locale=case.locale,
                currency=case.currency,
            )
        elif case.kind == "decimal":
            text = render_function(
                case.as_decimal_number(),
                locale=case.locale,
                form="decimal",
            )
        else:
            text = render_function(
                case.python_value(),
                locale=case.locale,
                form=case.kind,
            )
        return ExecutionResult.text_result(normalize(text))
    except Exception as exc:  # noqa: BLE001
        return ExecutionResult.exception_result(exc)


__all__ = ["normalize", "run_num2words", "run_numeralform"]
