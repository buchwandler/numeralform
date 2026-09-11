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
    "ordinal_num": "ordinal_num",
    "year": "year",
}
_RU_CASE_MAP = {
    "n": "nominative",
    "g": "genitive",
    "d": "dative",
    "a": "accusative",
    "i": "instrumental",
    "p": "prepositional",
}
_RU_CASE_ORACLE_MAP = {value: key for key, value in _RU_CASE_MAP.items()}
_GENDER_ORACLE_MAP = {"masculine": "m", "feminine": "f", "neuter": "n"}


def normalize(text: object) -> str:
    return unicodedata.normalize("NFC", str(text))


def num2words_call_kwargs(
    locale: str,
    kind: str,
    currency: str | None = None,
    options: dict[str, Any] | None = None,
    call_variant: str | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"lang": locale.replace("-", "_")}
    if call_variant == "ordinal-bool":
        kwargs["ordinal"] = True
    elif kind == "currency":
        kwargs.update(to="currency", currency=currency)
    else:
        kwargs["to"] = _NUM2WORDS_FORMS[kind]
    oracle_options = dict(options or {})
    language = locale.split("-", 1)[0]
    if "gender" in oracle_options:
        gender = str(oracle_options["gender"])
        oracle_options["gender"] = (
            _GENDER_ORACLE_MAP.get(gender, gender)
            if language in {"es", "ru"}
            else gender
        )
    if language == "ru":
        if "case" in oracle_options:
            oracle_options["case"] = _RU_CASE_ORACLE_MAP.get(
                str(oracle_options["case"]), oracle_options["case"]
            )
        if "grammatical_number" in oracle_options and "plural" not in oracle_options:
            oracle_options["plural"] = (
                oracle_options.pop("grammatical_number") == "plural"
            )
        if "animacy" in oracle_options and "animate" not in oracle_options:
            oracle_options["animate"] = oracle_options.pop("animacy") == "animate"
    kwargs.update(oracle_options)
    return kwargs


def num2words_kwargs(case: RandomCase) -> dict[str, Any]:
    return num2words_call_kwargs(
        case.oracle_locale,
        case.kind,
        case.currency,
        case.options,
        case.call_variant,
    )


def num2words_invocation(case: RandomCase) -> tuple[Any, dict[str, Any]]:
    """Build the single upstream invocation used by probes and execution."""
    return case.transport_value(), num2words_kwargs(case)


def oracle_supports_case(
    case: RandomCase, external_num2words: Callable[..., Any]
) -> bool:
    """Probe the exact value and keyword arguments used for a case."""
    try:
        value, kwargs = num2words_invocation(case)
        external_num2words(value, **kwargs)
    except Exception:  # noqa: BLE001
        return False
    return True


def canonical_call_kwargs(case: RandomCase) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if (
        case.locale.split("-", 1)[0] == "es"
        and case.kind == "ordinal"
        and "gender" in case.options
    ):
        kwargs["syntax"] = "attributive"
    if "gender" in case.options:
        gender = case.options["gender"]
        kwargs["gender"] = {"m": "masculine", "f": "feminine", "n": "neuter"}.get(
            str(gender), gender
        )
    if "case" in case.options:
        value = str(case.options["case"]).lower()
        kwargs["case"] = _RU_CASE_MAP.get(value, value)
    if "plural" in case.options:
        kwargs["grammatical_number"] = (
            "plural" if case.options["plural"] else "singular"
        )
    if "grammatical_number" in case.options:
        kwargs["grammatical_number"] = case.options["grammatical_number"]
    if "animate" in case.options:
        kwargs["animacy"] = "animate" if case.options["animate"] else "inanimate"
    if "animacy" in case.options:
        kwargs["animacy"] = case.options["animacy"]
    return kwargs


def run_num2words(
    case: RandomCase, external_num2words: Callable[..., Any]
) -> ExecutionResult:
    """Execute a case against the supplied, already verified oracle function."""
    try:
        value, kwargs = num2words_invocation(case)
        text = external_num2words(value, **kwargs)
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
            kwargs: dict[str, Any] = {
                "locale": case.locale,
                "currency": case.currency,
                "cents": bool(case.options.get("cents", True)),
            }
            if "separator" in case.options:
                kwargs["separator"] = case.options["separator"]
            text = render_currency_function(case.python_value(), **kwargs)
        elif case.kind == "decimal":
            text = render_function(
                case.as_decimal_number(), locale=case.locale, form="decimal"
            )
        else:
            text = render_function(
                case.python_value(),
                locale=case.locale,
                form=case.kind,
                **canonical_call_kwargs(case),
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
        value, kwargs = num2words_invocation(case)
        text = num2words_function(value, **kwargs)
        return ExecutionResult.text_result(normalize(text))
    except Exception as exc:  # noqa: BLE001
        return ExecutionResult.exception_result(exc)


run_numeralform = run_numeralform_canonical

__all__ = [
    "canonical_call_kwargs",
    "normalize",
    "num2words_call_kwargs",
    "num2words_invocation",
    "num2words_kwargs",
    "oracle_supports_case",
    "run_num2words",
    "run_numeralform",
    "run_numeralform_canonical",
    "run_numeralform_compat",
]
