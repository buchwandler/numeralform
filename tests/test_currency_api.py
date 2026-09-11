from __future__ import annotations

import inspect
from decimal import Decimal

import pytest

from numeralform import (
    CurrencyRequest,
    InvalidRequestError,
    InvalidValueError,
    LocaleFeatures,
    MoneyAmount,
    NumeralRequest,
    UnsupportedCurrencyError,
    realize_currency,
    render_currency,
    supports_currency,
)


def test_money_amount_preserves_embedded_currency():
    amount = MoneyAmount(1, 50, "usd")

    assert amount.currency == "USD"
    assert render_currency(amount) == "one dollar and fifty cents"
    result = realize_currency(amount)
    assert result.request.amount.currency == "USD"


def test_money_amount_conflicting_currency_is_rejected():
    amount = MoneyAmount(1, 50, "USD")

    with pytest.raises(InvalidRequestError):
        render_currency(amount, currency="EUR")
    with pytest.raises(InvalidRequestError):
        realize_currency(amount, currency="EUR")


def test_money_amount_validates_minor_units_before_minor_range():
    with pytest.raises(InvalidRequestError):
        MoneyAmount(1, 0, "EUR", minor_units="2")

    with pytest.raises(InvalidRequestError):
        render_currency(MoneyAmount(1, 0, "JPY", minor_units=2))


def test_currency_request_validates_runtime_fields():
    with pytest.raises(InvalidRequestError):
        CurrencyRequest(object(), "en")
    with pytest.raises(InvalidRequestError):
        CurrencyRequest(MoneyAmount(1, 0, "EUR"), "")
    with pytest.raises(InvalidRequestError):
        CurrencyRequest(MoneyAmount(1, 0, "EUR"), "en", cents=1)
    with pytest.raises(InvalidRequestError):
        CurrencyRequest(MoneyAmount(1, 0, "EUR"), "en", separator=1)


def test_currency_scale_behavior_for_zero_and_three_decimal_currencies():
    assert render_currency(Decimal("1.4"), locale="en", currency="JPY") == ("one yen")
    assert render_currency(Decimal("1.001"), locale="en", currency="KWD").endswith(
        "one fils"
    )
    assert render_currency(Decimal("1.001"), locale="en", currency="BHD").endswith(
        "one fils"
    )


def test_currency_errors_are_canonical():
    with pytest.raises(InvalidValueError):
        render_currency(True)
    with pytest.raises(InvalidValueError):
        render_currency("not numeric")
    with pytest.raises(InvalidRequestError):
        render_currency(1, separator=1)
    with pytest.raises(InvalidRequestError):
        render_currency(1, currency="EU!")
    with pytest.raises(UnsupportedCurrencyError):
        render_currency(1, currency="ZZZ")


def test_supports_currency_uses_canonical_locale_resolution():
    assert supports_currency("en_US", "usd")
    assert not supports_currency("zz", "EUR", allow_fallback=True)
    assert supports_currency("de-AT", "EUR", allow_fallback=True)
    assert not supports_currency("fi", "CHF", allow_fallback=False)


def test_supports_currency_matches_renderability_for_fallback():
    assert render_currency(1, locale="en_US", currency="USD")
    assert supports_currency("en_US", "USD")
    assert render_currency(1, locale="de-AT", currency="EUR")
    assert supports_currency("de-AT", "EUR", allow_fallback=True)


def test_locale_features_rejects_non_mapping_container():
    with pytest.raises(InvalidRequestError):
        LocaleFeatures((("foo", "bar"),))


def test_numeral_request_annotations_match_runtime_coercion():
    request = NumeralRequest(
        1, "en", form="cardinal", syntax="standalone", features={"dialect": "x"}
    )
    assert request.form.value == "cardinal"
    assert request.syntax.value == "standalone"
    assert request.features["dialect"] == "x"


def test_canonical_currency_signature_has_no_compatibility_switch():
    assert "compatibility" not in inspect.signature(render_currency).parameters
    assert "compatibility" not in inspect.signature(realize_currency).parameters
