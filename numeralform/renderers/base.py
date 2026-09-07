"""Renderer protocol and common request checks."""

from __future__ import annotations

from typing import Protocol

from ..errors import UnsupportedFormError, UnsupportedMorphologyError
from ..locale import LocaleCapabilities
from ..model import NumeralRequest, NumeralResult


class LocaleRenderer(Protocol):
    locale: str

    def capabilities(self) -> LocaleCapabilities: ...

    def render(self, request: NumeralRequest) -> NumeralResult: ...


def validate_request(request: NumeralRequest, capabilities: LocaleCapabilities) -> None:
    if request.form not in capabilities.forms:
        raise UnsupportedFormError(
            f"locale {request.locale!r} does not support {request.form.value} form"
        )
    if request.syntax not in capabilities.syntaxes:
        raise UnsupportedMorphologyError(
            f"locale {request.locale!r} does not support {request.syntax.value} syntax"
        )
    if request.style is not None and request.style not in capabilities.styles:
        raise UnsupportedMorphologyError(
            f"locale {request.locale!r} does not support style {request.style!r}"
        )
    morphology = request.morphology
    if morphology.gender is not None and morphology.gender not in capabilities.genders:
        raise UnsupportedMorphologyError(
            f"locale {request.locale!r} does not support gender {morphology.gender.value}"
        )
    if morphology.case is not None and morphology.case not in capabilities.cases:
        raise UnsupportedMorphologyError(
            f"locale {request.locale!r} does not support case {morphology.case.value}"
        )
    if morphology.animacy is not None and not capabilities.animacy:
        raise UnsupportedMorphologyError(
            f"locale {request.locale!r} does not support animacy"
        )
    if (
        morphology.grammatical_number is not None
        and not capabilities.grammatical_number
    ):
        raise UnsupportedMorphologyError(
            f"locale {request.locale!r} does not support grammatical number"
        )
    if morphology.noun_class is not None and not capabilities.noun_class:
        raise UnsupportedMorphologyError(
            f"locale {request.locale!r} does not support noun class"
        )
