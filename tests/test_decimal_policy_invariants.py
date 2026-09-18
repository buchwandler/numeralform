"""Invariant: non-English locales never silently fall back to English decimals."""

from __future__ import annotations

import pytest

from numeralform import DecimalNumber, render
from numeralform.locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from numeralform.model import NumeralForm, NumeralRequest, NumeralResult
from numeralform.registry import registered_locales, resolve
from numeralform.renderers._shared import (
    DecimalFallbackRenderer,
    LexicalRenderer,
    reviewed_decimal_policy,
)


def _is_lexical(renderer) -> bool:
    target = (
        renderer._delegate
        if isinstance(renderer, DecimalFallbackRenderer)
        else renderer
    )
    return isinstance(target, LexicalRenderer)


def test_every_lexical_decimal_capability_has_a_reviewed_policy():
    offenders = []
    for locale in registered_locales():
        renderer = resolve(locale)
        if not _is_lexical(renderer):
            continue
        capabilities = renderer.capabilities()
        has_decimal = NumeralForm.DECIMAL in capabilities.forms
        if has_decimal != (reviewed_decimal_policy(locale) is not None):
            offenders.append(locale)
    assert offenders == []


def test_decimal_rendering_has_no_english_fallback_words():
    sample = DecimalNumber("1", "20", False)
    negative = DecimalNumber("0", "01", True)
    for locale in registered_locales():
        if locale.startswith("en"):
            continue
        renderer = resolve(locale)
        if not _is_lexical(renderer):
            continue
        if NumeralForm.DECIMAL not in renderer.capabilities().forms:
            continue
        for value, is_negative in ((sample, False), (negative, True)):
            text = render(value, locale=locale, form="decimal")
            policy = reviewed_decimal_policy(locale)
            assert policy is not None
            words = text.split()
            if is_negative:
                assert text.startswith(policy.negative_prefix), (locale, text)
                words = text.removeprefix(policy.negative_prefix).split()
            assert policy.marker in words, (locale, text)
            assert "point" not in words, (locale, text)
            assert "minus" not in words or policy.negative_prefix == "minus", (
                locale,
                text,
            )


class _LegacyCardinalOnly:
    locale = "xx"

    def capabilities(self) -> LocaleCapabilities:
        return LocaleCapabilities(
            profiles=(
                CapabilityProfile(
                    NumeralForm.CARDINAL,
                    domain=NumericDomain(maximum=999),
                ),
            ),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        return NumeralResult(str(request.value), request.locale, request.form)


def test_fallback_renderer_does_not_invent_decimal_for_unreviewed_locale():
    fallback = DecimalFallbackRenderer(_LegacyCardinalOnly())
    assert NumeralForm.DECIMAL not in fallback.capabilities().forms


def test_decimal_policy_lookup_has_no_silent_fallback():
    assert reviewed_decimal_policy("en-GB") is not None
    assert reviewed_decimal_policy("xx") is None
    from numeralform.renderers._shared import decimal_policy

    with pytest.raises(LookupError):
        decimal_policy("xx")
