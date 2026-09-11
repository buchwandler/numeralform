from __future__ import annotations

import inspect

import pytest

from numeralform import LocaleFeatures, NumeralRequest, NumeralResult, realize, render
from numeralform.errors import InvalidRequestError, InvalidValueError


def test_provisional_renderer_registry_is_not_top_level_api():
    import numeralform

    for name in ("register_locale", "registered_locales", "resolve"):
        assert name not in numeralform.__all__
        assert not hasattr(numeralform, name)


def test_render_has_explicit_keywords():
    parameters = inspect.signature(render).parameters
    assert "form" in parameters
    assert "syntax" in parameters
    assert "morphology" in parameters
    assert "options" not in parameters


def test_locale_features_mapping_and_object_are_equivalent():
    assert render(1, locale="en", features={}) == render(
        1, locale="en", features=LocaleFeatures()
    )


def test_form_inference_and_explicit_conflict():
    from numeralform import DecimalNumber

    value = DecimalNumber("1", "20")
    assert realize(value, locale="en").form.value == "decimal"
    with pytest.raises(InvalidValueError):
        render(value, locale="en", form="cardinal")


def test_result_contains_effective_request_metadata():
    result = realize(42, locale="en-US", syntax="standalone")
    assert isinstance(result, NumeralResult)
    assert result.requested_locale == "en-US"
    assert result.locale == "en-US"
    british = realize(42, locale="en-GB", syntax="standalone")
    assert british.requested_locale == "en-GB"
    assert british.locale == "en-GB"
    assert british.style == "default"
    assert result.style == "default"
    assert result.syntax.value == "standalone"
    assert result.features == LocaleFeatures()


def test_request_rejects_rendering_options():
    request = NumeralRequest(42, "en")
    with pytest.raises(InvalidRequestError):
        realize(request, style="default")


def test_unknown_keyword_is_rejected():
    with pytest.raises(TypeError):
        render(1, locale="en", unknown=True)
