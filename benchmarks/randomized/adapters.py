"""Implementation-specific adapters for randomized differential cases."""

from __future__ import annotations

import unicodedata
from collections.abc import Callable
from typing import Any

from numeralform import render, render_currency
from numeralform.compat import num2words as compat_num2words

from .model import ExecutionResult, RandomCase

_NUM2WORDS_FORMS = {
    "cardinal": "cardinal",
    "decimal": "cardinal",
    "ordinal": "ordinal",
    "year": "year",
}


def normalize(text: object) -> str:
    return unicodedata.normalize("NFC", str(text))


def num2words_call_kwargs(
    locale: str, kind: str, currency: str | None = None
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"lang": locale.replace("-", "_")}
    if kind == "currency":
        kwargs.update(to="currency", currency=currency)
    else:
        kwargs["to"] = _NUM2WORDS_FORMS[kind]
    return kwargs


def num2words_kwargs(case: RandomCase) -> dict[str, Any]:
    return num2words_call_kwargs(case.oracle_locale, case.kind, case.currency)


def run_num2words(
    case: RandomCase, external_num2words: Callable[..., Any]
) -> ExecutionResult:
    """Execute a case against the supplied, already verified oracle function."""
    try:
        text = external_num2words(case.python_value(), **num2words_kwargs(case))
        return ExecutionResult.text_result(normalize(text))
    except Exception as exc:  # noqa: BLE001
        return ExecutionResult.exception_result(exc)


def run_numeralform_canonical(
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


def run_numeralform_compat(
    case: RandomCase,
    *,
    num2words_function: Callable[..., Any] = compat_num2words,
) -> ExecutionResult:
    """Execute a case through the num2words-shaped compatibility API."""
    try:
        text = num2words_function(case.python_value(), **num2words_kwargs(case))
        return ExecutionResult.text_result(normalize(text))
    except Exception as exc:  # noqa: BLE001
        return ExecutionResult.exception_result(exc)


# Kept as a source-compatible alias for callers of the pre-target benchmark API.
run_numeralform = run_numeralform_canonical


__all__ = [
    "normalize",
    "num2words_call_kwargs",
    "num2words_kwargs",
    "run_num2words",
    "run_numeralform",
    "run_numeralform_canonical",
    "run_numeralform_compat",
]
