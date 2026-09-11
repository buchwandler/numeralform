from decimal import Decimal

import pytest

from benchmarks.randomized.adapters import (
    num2words_call_kwargs,
    run_numeralform_canonical,
)
from benchmarks.randomized.generator import (
    _currency_edge_values,
    _ordinal_edge_values,
    _year_edge_values,
    generate_cases,
)
from benchmarks.randomized.model import CASE_KINDS, RandomCase, SerializedRandomValue


def make_case(kind="currency", value=Decimal("1.20"), **kwargs):
    return RandomCase(
        3,
        3,
        7,
        0,
        "case-expansion",
        "en-GB",
        kind,
        str(value),
        SerializedRandomValue.from_python(value),
        kwargs.pop("currency", "USD") if kind == "currency" else None,
        options=kwargs,
    )


def test_ordinal_num_is_a_first_class_kind_and_round_trips_options():
    assert "ordinal_num" in CASE_KINDS
    case = RandomCase(
        3,
        3,
        7,
        0,
        "case-expansion",
        "en-GB",
        "currency",
        "1.20",
        SerializedRandomValue.from_python(Decimal("1.20")),
        "USD",
        options={"cents": False, "separator": " and"},
        variant_id="terse-literal-and",
        transport="native",
    )
    assert RandomCase.from_dict(case.to_dict()) == case


def test_old_payload_defaults_new_replay_fields():
    payload = make_case().to_dict()
    for key in ("options", "variant_id", "call_variant", "transport"):
        payload.pop(key)
    restored = RandomCase.from_dict(payload)
    assert restored.options == {}
    assert restored.variant_id is None
    assert restored.call_variant is None
    assert restored.transport == "native"


def test_invalid_option_for_kind_is_rejected():
    with pytest.raises(ValueError):
        RandomCase(
            3,
            3,
            1,
            0,
            "bad",
            "en",
            "ordinal_num",
            "1",
            SerializedRandomValue.from_python(1),
            options={"cents": False},
        )


def test_identity_distinguishes_currency_options():
    first = make_case(cents=True)
    second = make_case(cents=False)
    assert first.identity != second.identity


def test_ordinal_num_generation_filter_and_edges():
    cases, _, _ = generate_cases(
        seed=7,
        count=20,
        canonical_locales=("en",),
        external_locales=("en",),
        locales=("en",),
        kinds=("ordinal_num",),
        supports=lambda *args, **kwargs: True,
        currency_supports=lambda *args, **kwargs: True,
        oracle_supports=lambda *args, **kwargs: True,
    )
    assert all(case.kind == "ordinal_num" for case in cases)
    assert {0, 11, 102, 1003, 9999} <= set(_ordinal_edge_values())


def test_year_edges_cover_old_and_new_ranges():
    assert 905 in _year_edge_values()
    assert any(value < 1000 for value in _year_edge_values())
    assert any(value > 2099 for value in _year_edge_values())


def test_currency_edges_are_scale_aware():
    assert all(value == value.to_integral_value() for value in _currency_edge_values(0))
    assert Decimal("1.01") in _currency_edge_values(2)


def test_ordinal_num_adapter_dispatches_to_upstream_form():
    assert num2words_call_kwargs("en", "ordinal_num") == {"lang": "en", "to": "ordinal_num"}


def test_currency_options_are_passed_without_normalization():
    case = make_case(cents=False, separator=" +")
    seen = []
    result = run_numeralform_canonical(
        case,
        render_currency_function=lambda value, **kwargs: seen.append((value, kwargs)) or "ok",
    )
    assert result.text == "ok"
    assert seen == [(Decimal("1.20"), {"locale": "en-GB", "currency": "USD", "cents": False, "separator": " +"})]


def test_compatibility_call_variants_are_target_specific():
    canonical, _, _ = generate_cases(
        seed=4,
        count=30,
        canonical_locales=("en",),
        external_locales=("en",),
        locales=("en",),
        kinds=("ordinal",),
        supports=lambda *args, **kwargs: True,
        currency_supports=lambda *args, **kwargs: True,
        oracle_supports=lambda *args, **kwargs: True,
        target="canonical",
    )
    compat, _, _ = generate_cases(
        seed=4,
        count=30,
        canonical_locales=("en",),
        external_locales=("en",),
        locales=("en",),
        kinds=("ordinal",),
        supports=lambda *args, **kwargs: True,
        currency_supports=lambda *args, **kwargs: True,
        oracle_supports=lambda *args, **kwargs: True,
        target="compat",
    )
    assert all(case.call_variant is None and case.transport == "native" for case in canonical)
    assert any(case.call_variant == "ordinal-bool" for case in compat)


def test_structured_options_round_trip_and_use_new_profile_name():
    case = make_case(kind="cardinal", value=1, prefer=("nominative", "partitive"), definite=None)
    payload = case.to_dict()
    assert payload["option_profile_id"] is None
    restored = RandomCase.from_dict(payload)
    assert restored.options == {"definite": None, "prefer": ("nominative", "partitive")}


def test_new_option_profile_payload_is_backward_compatible():
    payload = make_case().to_dict()
    payload.pop("variant_id")
    payload["option_profile_id"] = "profile-1"
    assert RandomCase.from_dict(payload).variant_id == "profile-1"
