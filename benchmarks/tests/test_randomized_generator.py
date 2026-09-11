from decimal import Decimal
import pytest

from benchmarks.randomized.generator import (
    SharedLocale,
    generate_cases,
    shared_locale_pairs,
    shared_locales,
)
from benchmarks.randomized.model import RandomCase, SerializedRandomValue


def test_generation_is_seeded_and_filters_are_respected():
    kwargs = {
        "seed": 42,
        "count": 12,
        "canonical_locales": ("en", "de"),
        "external_locales": ("en", "de", "fr"),
        "locales": ("de",),
        "kinds": ("decimal",),
        "supports": lambda locale, kind, value: True,
        "currency_supports": lambda locale, value, currency: True,
    }
    first, _, _ = generate_cases(**kwargs)
    second, _, _ = generate_cases(**kwargs)
    assert first == second
    assert all(case.locale == "de" and case.kind == "decimal" for case in first)
    assert all(case.python_value() == Decimal(case.value.value) for case in first)


def test_shared_locales_normalizes_regional_spellings():
    assert shared_locales(
        canonical_locales=("en-IN", "de"), external_locales=("en_IN", "de")
    ) == (
        "de",
        "en-IN",
    )


def test_shared_locale_pairs_route_pinned_english_to_gb():
    assert shared_locale_pairs(
        canonical_locales=("en", "en-US", "en-GB", "de"),
        external_locales=("en", "de"),
    ) == (
        SharedLocale("de", "de"),
        SharedLocale("en-GB", "en"),
    )


def test_requested_oracle_english_locale_routes_to_shared_gb_pair():
    cases, _, _ = generate_cases(
        seed=5,
        count=3,
        canonical_locales=("en", "en-US", "en-GB"),
        external_locales=("en",),
        locales=("en",),
        kinds=("cardinal",),
        supports=lambda locale, kind, value: True,
        currency_supports=lambda locale, value, currency: True,
        oracle_supports=lambda locale, kind, value, currency: True,
    )

    assert {case.locale for case in cases} == {"en-GB"}
    assert {case.oracle_locale for case in cases} == {"en"}


def test_requested_canonical_shared_locale_wins_over_oracle_alias():
    cases, _, _ = generate_cases(
        seed=5,
        count=1,
        canonical_locales=("en",),
        external_locales=("en",),
        locales=("en",),
        kinds=("cardinal",),
        supports=lambda *args: True,
        currency_supports=lambda *args: True,
        oracle_supports=lambda *args: True,
    )

    assert cases[0].locale == "en"
    assert cases[0].oracle_locale == "en"


def test_shared_profile_filters_oracle_unsupported_candidates():
    calls = []

    def oracle_supports(locale, kind, value, currency):
        calls.append((locale, kind, value, currency))
        return len(calls) > 2

    cases, rejected, config = generate_cases(
        seed=7,
        count=5,
        profile="shared",
        canonical_locales=("en",),
        external_locales=("en",),
        locales=("en",),
        kinds=("cardinal",),
        supports=lambda locale, kind, value: True,
        currency_supports=lambda locale, value, currency: True,
        oracle_supports=oracle_supports,
    )

    assert len(cases) == 5
    assert config.profile == "shared"
    assert len(calls) >= 3
    assert rejected["generation_rejected_oracle_unsupported"] >= 2


def test_shared_jpy_generation_uses_integral_amounts_and_exact_spelling():
    cases, _, _ = generate_cases(
        seed=3,
        count=20,
        profile="shared",
        canonical_locales=("en",),
        external_locales=("en",),
        locales=("en",),
        kinds=("currency",),
        currencies=("JPY",),
        supports=lambda locale, kind, value: True,
        currency_supports=lambda locale, value, currency: True,
    )
    assert all(
        case.python_value() == case.python_value().to_integral_value() for case in cases
    )
    assert all("." not in case.value.value for case in cases)
    assert all(case.oracle_locale == "en" for case in cases)


def test_decimal_serialization_preserves_whole_number_spelling():
    assert SerializedRandomValue.from_python(Decimal(61)).to_dict() == {
        "kind": "decimal",
        "value": "61",
    }
    assert SerializedRandomValue.from_python(Decimal("61.0")).value == "61.0"


def test_v1_replay_without_oracle_locale_defaults_to_canonical_locale():
    case = RandomCase.from_dict(
        {
            "schema_version": 1,
            "generator_version": 1,
            "seed": 1,
            "index": 0,
            "case_id": "random-v1:1:000000",
            "locale": "en",
            "kind": "cardinal",
            "surface": "1",
            "value": {"kind": "int", "value": "1"},
            "currency": None,
            "tags": [],
        }
    )
    assert case.oracle_locale == "en"


def test_shared_exclusions_skip_incomparable_japanese_years():
    with pytest.raises(RuntimeError):
        generate_cases(
            seed=11,
            count=1,
            profile="shared",
            canonical_locales=("ja",),
            external_locales=("ja",),
            locales=("ja",),
            kinds=("year",),
            supports=lambda *args: True,
            currency_supports=lambda *args: True,
            oracle_supports=lambda *args: True,
        )
