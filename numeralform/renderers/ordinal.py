"""Locale-owned numeric ordinal notation strategies."""

from __future__ import annotations

from dataclasses import replace

from ..locale import CapabilityProfile, LocaleCapabilities
from ..model import Gender, NumeralForm, NumeralRequest, NumeralResult
from .base import LocaleRenderer, validate_request


class OrdinalNotationRenderer:
    """Delegate normal rendering while owning the numeric-ordinal surface."""

    def __init__(self, locale: str, delegate: LocaleRenderer):
        self.locale = locale
        self._delegate = delegate

    def capabilities(self) -> LocaleCapabilities:
        base = self._delegate.capabilities()
        language = self.locale.split("-", 1)[0]
        genders = (
            frozenset({Gender.MASCULINE, Gender.FEMININE})
            if language in {"es", "fr", "pt"}
            else frozenset()
        )
        profile = CapabilityProfile(NumeralForm.ORDINAL_NUMERIC, genders=genders)
        return replace(
            base,
            profiles=tuple(base.profiles) + (profile,),
            notes=tuple(base.notes)
            + ("Numeric ordinal notation is provided by a locale-owned strategy.",),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        if request.form is not NumeralForm.ORDINAL_NUMERIC:
            return self._delegate.render(request)
        capabilities = self.capabilities()
        validate_request(request, capabilities)
        value = request.value
        language = self.locale.split("-", 1)[0]
        gender = request.morphology.gender
        if language == "en":
            suffix = (
                "th"
                if 10 <= value % 100 <= 20
                else {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
            )
            text = f"{value}{suffix}"
        elif language == "es":
            text = f"{value}{'ª' if gender is Gender.FEMININE else 'º'}"
        elif language == "fr":
            text = f"{value}{'er' if value == 1 and gender is not Gender.FEMININE else 'me'}"
        elif language == "eo":
            text = f"{value}a"
        elif language == "fa":
            text = f"{value}م"
        elif language in {"ja", "zh"}:
            text = f"第{value}"
        elif language == "pt":
            text = f"{value}.ª" if gender is Gender.FEMININE else f"{value}.º"
        else:
            text = f"{value}."
        return NumeralResult(
            text, request.locale, request.form, request.style, request.morphology
        )

    def __getattr__(self, name):
        return getattr(self._delegate, name)
