"""Locale-owned numeric ordinal notation strategies."""

from __future__ import annotations

from dataclasses import replace

from ..locale import CapabilityProfile, LocaleCapabilities
from ..model import Gender, NumeralForm, NumeralRequest, NumeralResult
from .base import LocaleRenderer, require_int, validate_request

_DEVANAGARI_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")
_BENGALI_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
_KANNADA_DIGITS = str.maketrans("0123456789", "೦೧೨೩೪೫೬೭೮೯")


def _render_numeric_ordinal(language: str, value: int, gender: Gender | None) -> str:
    if language == "en":
        suffix = (
            "th"
            if 10 <= value % 100 <= 20
            else {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
        )
        return f"{value}{suffix}"
    if language == "es":
        return f"{value}{'ª' if gender is Gender.FEMININE else 'º'}"
    if language == "fr":
        return (
            f"{value}{'er' if value == 1 and gender is not Gender.FEMININE else 'me'}"
        )
    if language == "eo":
        return f"{value}a"
    if language == "fa":
        return f"{value}م"
    if language in {"ja", "zh"}:
        return f"第{value}"
    if language == "ko":
        return f"{value}번째"
    if language == "am":
        return f"{value}ኛ"
    if language == "az":
        suffix = {
            0: "cı",
            1: "ci",
            2: "ci",
            3: "cü",
            4: "cı",
            5: "cı",
            6: "cı",
            7: "cı",
            8: "cı",
            9: "cı",
        }[value % 10]
        return f"{value}{suffix}"
    if language == "ce":
        return f"{value}-й"
    if language == "ca":
        suffix = {1: "r", 2: "n", 3: "r"}.get(value % 10, "è")
        return f"{value}{suffix}"
    if language == "da":
        suffix = "en" if value % 10 == 2 else "ende" if value % 10 == 3 else "te"
        return f"{value}{suffix}"
    if language == "id":
        return f"ke-{value}"
    if language == "nl":
        return f"{value}e"
    if language == "ro":
        return f"{value}-lea" if value == 1 else f"al {value}-lea"
    if language == "te":
        return f"{value}వ"
    if language == "tet":
        return f"{value}º"
    if language == "tg":
        return f"{value}{'юм' if value % 10 == 3 else 'ум'}"
    if language == "tr":
        suffixes = {
            0: "ıncı",
            1: "inci",
            2: "inci",
            3: "üncü",
            4: "üncü",
            5: "inci",
            6: "ıncı",
            7: "inci",
            8: "inci",
            9: "uncu",
        }
        return f"{value}{suffixes[value % 10]}"
    if language == "hi":
        return f"{str(value).translate(_DEVANAGARI_DIGITS)}वाँ"
    if language == "bn":
        return f"{str(value).translate(_BENGALI_DIGITS)}তম"
    if language == "kn":
        return f"{str(value).translate(_KANNADA_DIGITS)}ನೆಯ"
    if language == "hy":
        return f"{value}-րդ"
    if language == "mn":
        return f"{value}-р"
    if language == "pt":
        return f"{value}.ª" if gender is Gender.FEMININE else f"{value}.º"
    return f"{value}."


class OrdinalNotationRenderer:
    """Delegate normal rendering while owning the numeric-ordinal surface."""

    def __init__(self, locale: str, delegate: LocaleRenderer):
        self.locale = locale
        self._delegate = delegate

    def capabilities(self) -> LocaleCapabilities:
        base = self._delegate.capabilities()
        if any(
            profile.form is NumeralForm.ORDINAL_NUMERIC for profile in base.profiles
        ):
            return base
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
        value = require_int(request.value)
        language = self.locale.split("-", 1)[0]
        text = _render_numeric_ordinal(language, value, request.morphology.gender)
        return NumeralResult(
            text, request.locale, request.form, request.style, request.morphology
        )

    def __getattr__(self, name):
        return getattr(self._delegate, name)
