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


def test_italian_currency_lexemes_do_not_fall_back_to_english() -> None:
    assert render_currency(Decimal("1.50"), locale="it", currency="USD") == (
        "un dollaro e cinquanta centesimi"
    )
    assert render_currency(Decimal("1.50"), locale="it", currency="GBP") == (
        "una sterlina e cinquanta pence"
    )
    assert render_currency(Decimal("1.50"), locale="it", currency="CHF") == (
        "un franco svizzero e cinquanta centesimi"
    )


def test_currency_request_validates_omit_zero_minor_and_preserves_default() -> None:
    with pytest.raises(InvalidRequestError):
        CurrencyRequest(MoneyAmount(1, 0, "EUR"), "en", omit_zero_minor=1)

    assert render_currency(1, locale="en", currency="USD") == (
        "one dollar and zero cents"
    )
    assert (
        render_currency(1, locale="en", currency="USD", omit_zero_minor=True)
        == "one dollar"
    )

    request = CurrencyRequest(MoneyAmount(1, 0, "USD"), "en", omit_zero_minor=True)
    result = realize_currency(request)
    assert result.text == "one dollar"
    assert result.request.omit_zero_minor is True


def test_spanish_currency_attributive_major_agreement() -> None:
    assert (
        render_currency(1, locale="es", currency="EUR", omit_zero_minor=True)
        == "un euro"
    )
    assert (
        render_currency(1, locale="es-MX", currency="USD", omit_zero_minor=True)
        == "un dólar"
    )
    assert (
        render_currency(1, locale="es", currency="GBP", omit_zero_minor=True)
        == "una libra"
    )


def test_german_chf_uses_native_terminology() -> None:
    text = render_currency(Decimal("87.50"), locale="de", currency="CHF")
    assert "Swiss" not in text
    assert "Schweizer Franken" in text
    assert "Rappen" in text


def test_new_currency_morphology_and_support_matrix() -> None:
    assert (
        render_currency(50_000, locale="es-MX", currency="KRW", omit_zero_minor=True)
        == "cincuenta mil wones"
    )
    assert (
        render_currency(1_000_000, locale="es-MX", currency="VND", omit_zero_minor=True)
        == "un millón de dongs"
    )
    assert (
        render_currency(50_000, locale="es-MX", currency="MNT", omit_zero_minor=True)
        == "cincuenta mil tugriks"
    )
    assert (
        render_currency(2_000_000, locale="es-MX", currency="MXN", omit_zero_minor=True)
        == "dos millones de pesos"
    )
    assert render_currency(
        1_250_000, locale="es-MX", currency="MXN", omit_zero_minor=True
    ) == ("un millón doscientos cincuenta mil pesos")

    for locale, currency in (
        ("es-MX", "MXN"),
        ("es-MX", "KRW"),
        ("es-MX", "VND"),
        ("es-MX", "MNT"),
        ("de", "CHF"),
    ):
        assert supports_currency(locale, currency, allow_fallback=False)
