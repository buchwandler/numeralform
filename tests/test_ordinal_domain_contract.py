"""Ordinal capability-domain contract tests.

Every advertised word-ordinal domain must be an executable contract:

- no profile advertises negative ordinals;
- every finite domain boundary renders;
- ``supports()`` and ``render()`` agree at the boundaries;
- every integer inside the intersection of a domain with the common sweep
  range renders;
- fixture-only locales advertise exactly their largest contiguous reviewed
  fixture block.
"""

from __future__ import annotations

import pytest

from numeralform import (
    NumeralForm,
    capabilities,
    locales,
    render,
    supports,
)
from numeralform.errors import NumeralFormError
from numeralform.registry import resolve
from numeralform.renderers._shared import LexicalRenderer

ORDINAL = NumeralForm.ORDINAL

# Base languages whose word ordinals are produced by a locale-owned
# algorithm rather than reviewed fixture lookup. Regional variants
# (en-GB, es-MX, fr-BE, ...) inherit the classification.
ALGORITHMIC_ORDINAL_LANGUAGES = {
    "de",
    "en",
    "es",
    "fi",
    "fr",
    "it",
    "ja",
    "ko",
    "pt",
    "ru",
    "sv",
    "zh",
}

COMMON_SWEEP_LIMIT = 9_999


def _ordinal_domains(locale: str):
    return {
        profile.domain
        for profile in capabilities(locale).profiles
        if profile.form is ORDINAL
    }


def _locales_with_ordinals() -> list[str]:
    return [locale for locale in locales() if _ordinal_domains(locale)]


def _algorithmic(locale: str) -> bool:
    return locale.split("-", 1)[0] in ALGORITHMIC_ORDINAL_LANGUAGES


def _unwrap(renderer):
    while (delegate := getattr(renderer, "_delegate", None)) is not None:
        renderer = delegate
    return renderer


def _base_renderer(locale: str):
    return _unwrap(resolve(locale))


def _contiguous_block(values) -> tuple[int, int] | None:
    if not values:
        return None
    minimum = min(values)
    maximum = minimum
    while maximum + 1 in values:
        maximum += 1
    return minimum, maximum


def _assert_renders(locale: str, value: int) -> None:
    assert supports(locale, form=ORDINAL, value=value), (
        f"{locale}: supports() rejected advertised ordinal value {value}"
    )
    text = render(value, locale=locale, form=ORDINAL)
    assert text, f"{locale}: ordinal {value} rendered empty"


def _assert_rejects(locale: str, value: int) -> None:
    assert not supports(locale, form=ORDINAL, value=value), (
        f"{locale}: supports() advertised ordinal value {value} outside the domain"
    )
    with pytest.raises(NumeralFormError):
        render(value, locale=locale, form=ORDINAL)


def test_no_ordinal_profile_advertises_negatives_or_negative_minimum():
    for locale in _locales_with_ordinals():
        for domain in _ordinal_domains(locale):
            assert domain.allow_negative is False, f"{locale}: {domain}"
            assert domain.minimum is None or domain.minimum >= 0, f"{locale}: {domain}"
            assert domain.maximum is not None, (
                f"{locale}: ordinal profile {domain} is unbounded but every "
                "implementation is finite"
            )


def test_ordinal_domain_boundaries_are_executable():
    for locale in _locales_with_ordinals():
        for domain in _ordinal_domains(locale):
            minimum = domain.minimum or 0
            maximum = domain.maximum
            _assert_renders(locale, minimum)
            _assert_renders(locale, maximum)
            _assert_rejects(locale, maximum + 1)
            _assert_rejects(locale, -1)


@pytest.mark.parametrize("locale", _locales_with_ordinals())
def test_common_ordinal_sweep(locale):
    for domain in _ordinal_domains(locale):
        minimum = domain.minimum or 0
        for value in range(minimum, min(domain.maximum, COMMON_SWEEP_LIMIT) + 1):
            _assert_renders(locale, value)


SCALE_PROBES = (
    9_999,
    10_000,
    10_001,
    99_999,
    100_000,
    100_001,
    999_999,
    1_000_000,
    1_000_001,
    999_999_999,
    1_000_000_000,
    999_999_999_999,
    9999_9999_9999,
    10**18 - 1,
)


@pytest.mark.parametrize("locale", _locales_with_ordinals())
def test_algorithmic_scale_probes(locale):
    if not _algorithmic(locale):
        pytest.skip("fixture-only locale: contiguous sweep already exhausts it")
    for domain in _ordinal_domains(locale):
        probes = [value for value in SCALE_PROBES if value <= domain.maximum]
        probes += [domain.maximum - 1, domain.maximum]
        for value in probes:
            _assert_renders(locale, value)


@pytest.mark.parametrize("locale", _locales_with_ordinals())
def test_fixture_only_domains_are_continuous_and_complete(locale):
    if _algorithmic(locale):
        pytest.skip("locale-owned ordinal algorithm")
    renderer = _base_renderer(locale)
    assert isinstance(renderer, LexicalRenderer)
    ordinals = renderer.ordinals
    block = _contiguous_block(ordinals)
    for domain in _ordinal_domains(locale):
        assert block is not None, f"{locale}: ordinal profile without fixtures"
        assert domain.minimum == block[0], f"{locale}: {domain} vs fixtures {block}"
        assert domain.maximum == block[1], f"{locale}: {domain} vs fixtures {block}"
        assert set(range(block[0], block[1] + 1)) <= set(ordinals)


@pytest.mark.parametrize("locale", _locales_with_ordinals())
def test_isolated_fixtures_do_not_widen_domains(locale):
    for domain in _ordinal_domains(locale):
        if domain.maximum is None or 2024 <= domain.maximum:
            continue
        _assert_rejects(locale, 2024)


def test_known_previous_suffix_leakages():
    # Chinese owns the 第 + cardinal ordinal rule; the old shared fallback
    # appended the English suffix here.
    assert render(1001, locale="zh", form=ORDINAL) == "第一千零一"
    # Generic fixture-only locales no longer synthesize values beyond their
    # reviewed contiguous block instead of rendering "...th" cardinals.
    for locale in ("am", "ar", "be", "bn", "he", "kn", "uk"):
        assert not supports(locale, form=ORDINAL, value=1001)


@pytest.mark.parametrize(
    ("locale", "block"),
    [("hi", (0, 3)), ("hy", (1, 3)), ("kk", (1, 3)), ("mn", (1, 3))],
)
def test_sparse_fixture_locales_advertise_only_contiguous_block(locale, block):
    # These locales have a tiny contiguous block plus isolated reference
    # fixtures (10, 42, 100, 1000, 2024). Only the contiguous block may be
    # advertised as a continuous domain; isolated keys must stay rejected.
    assert _contiguous_block(_base_renderer(locale).ordinals) == block
    for domain in _ordinal_domains(locale):
        assert (domain.minimum, domain.maximum) == block
    for isolated in (block[1] + 1, 10, 42, 100, 1000, 2024):
        _assert_rejects(locale, isolated)
