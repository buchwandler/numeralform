"""Locale parsing, canonicalization, and capability declarations."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .errors import InvalidRequestError
from .model import Case, Gender, NumeralForm, Syntax

_LOCALE_RE = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{2,8})*$")
_ALIASES = {"jp": "ja", "cn": "zh-CN"}


def _normalize_open_values(values) -> frozenset[str | Case]:
    normalized = set()
    for value in values:
        if isinstance(value, Case):
            normalized.add(value)
        elif isinstance(value, str) and value.strip():
            try:
                normalized.add(Case(value.strip().lower()))
            except ValueError:
                normalized.add(value.strip().lower())
        else:
            raise InvalidRequestError("capability feature values must be non-empty strings")
    return frozenset(normalized)


def _normalize_string_values(values) -> frozenset[str]:
    normalized = set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise InvalidRequestError("capability feature values must be non-empty strings")
        normalized.add(value.strip().lower())
    return frozenset(normalized)


@dataclass(frozen=True, slots=True)
class NumericDomain:
    minimum: int | None = None
    maximum: int | None = None
    allow_negative: bool = True
    decimals: bool = False
    fractions: bool = False

    def __post_init__(self) -> None:
        if self.minimum is not None and (
            isinstance(self.minimum, bool) or not isinstance(self.minimum, int)
        ):
            raise InvalidRequestError("numeric domain minimum must be an integer or None")
        if self.maximum is not None and (
            isinstance(self.maximum, bool) or not isinstance(self.maximum, int)
        ):
            raise InvalidRequestError("numeric domain maximum must be an integer or None")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise InvalidRequestError("numeric domain minimum cannot exceed maximum")
        if not isinstance(self.allow_negative, bool):
            raise InvalidRequestError("numeric domain allow_negative must be a boolean")
        if not isinstance(self.decimals, bool) or not isinstance(self.fractions, bool):
            raise InvalidRequestError("numeric domain decimal/fraction flags must be booleans")

    def accepts_integer(self, value: int) -> bool:
        return (
            (self.minimum is None or value >= self.minimum)
            and (self.maximum is None or value <= self.maximum)
            and (self.allow_negative or value >= 0)
        )


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    name: str
    values: frozenset[str] = frozenset()
    boolean: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidRequestError("feature specification name must be non-empty")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "values", _normalize_string_values(self.values))
        if not isinstance(self.boolean, bool):
            raise InvalidRequestError("feature specification boolean must be a boolean")
        if self.boolean and self.values:
            raise InvalidRequestError("boolean feature specifications cannot enumerate values")


@dataclass(frozen=True, slots=True)
class Locale:
    language: str
    script: str | None = None
    region: str | None = None
    variants: tuple[str, ...] = ()

    @property
    def tag(self) -> str:
        parts = [self.language]
        if self.script:
            parts.append(self.script)
        if self.region:
            parts.append(self.region)
        parts.extend(self.variants)
        return "-".join(parts)


def canonicalize_locale(locale: str) -> str:
    if not isinstance(locale, str) or not locale.strip():
        raise InvalidRequestError("locale must be a non-empty string")
    value = locale.strip().replace("_", "-")
    value = _ALIASES.get(value.lower(), value)
    if not _LOCALE_RE.fullmatch(value):
        raise InvalidRequestError(f"invalid locale identifier: {locale!r}")
    parts = value.split("-")
    language = parts[0].lower()
    normalized = [language]
    for part in parts[1:]:
        if len(part) == 4 and part.isalpha():
            normalized.append(part.title())
        elif len(part) in (2, 3) and part.isalnum():
            normalized.append(part.upper())
        else:
            normalized.append(part.lower())
    return "-".join(normalized)


def parse_locale(locale: str) -> Locale:
    parts = canonicalize_locale(locale).split("-")
    language = parts.pop(0)
    script = None
    region = None
    if parts and len(parts[0]) == 4:
        script = parts.pop(0)
    if parts and len(parts[0]) in (2, 3):
        region = parts.pop(0)
    return Locale(language, script, region, tuple(parts))


def fallback_chain(locale: str | Locale) -> tuple[str, ...]:
    parsed = locale if isinstance(locale, Locale) else parse_locale(locale)
    chain = [parsed.tag]
    if parsed.variants:
        chain.append(Locale(parsed.language, parsed.script, parsed.region).tag)
    if parsed.region:
        chain.append(Locale(parsed.language, parsed.script).tag)
    if parsed.script:
        chain.append(Locale(parsed.language).tag)
    elif not parsed.region:
        chain.append(parsed.language)
    return tuple(dict.fromkeys(chain))


@dataclass(frozen=True, slots=True)
class CapabilityProfile:
    """Capabilities for one form in one or more compatible contexts."""

    form: NumeralForm
    syntaxes: frozenset[Syntax] = frozenset({Syntax.STANDALONE})
    genders: frozenset[Gender] = frozenset()
    cases: frozenset[str | Case] = frozenset()
    animacies: frozenset[str] = frozenset()
    grammatical_numbers: frozenset[str] = frozenset()
    noun_classes: frozenset[str] = frozenset()
    definitenesses: frozenset[str] = frozenset()
    states: frozenset[str] = frozenset()
    styles: frozenset[str] = frozenset({"default"})
    features: tuple[FeatureSpec, ...] = ()
    domain: NumericDomain = NumericDomain()
    # Compatibility constructor fields for renderers written against the old API.
    animacy: bool = False
    grammatical_number: bool = False
    noun_class: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "form", NumeralForm.coerce(self.form))
        object.__setattr__(self, "syntaxes", frozenset(Syntax.coerce(item) for item in self.syntaxes))
        object.__setattr__(self, "genders", frozenset(Gender.coerce(item) for item in self.genders))
        object.__setattr__(self, "cases", _normalize_open_values(self.cases))
        animacies = _normalize_string_values(self.animacies)
        numbers = _normalize_string_values(self.grammatical_numbers)
        noun_classes = _normalize_string_values(self.noun_classes)
        definitenesses = _normalize_string_values(self.definitenesses)
        states = _normalize_string_values(self.states)
        if self.animacy and not animacies:
            animacies = frozenset({"*"})
        if self.grammatical_number and not numbers:
            numbers = frozenset({"*"})
        if self.noun_class and not noun_classes:
            noun_classes = frozenset({"*"})
        object.__setattr__(self, "animacies", animacies)
        object.__setattr__(self, "grammatical_numbers", numbers)
        object.__setattr__(self, "noun_classes", noun_classes)
        object.__setattr__(self, "definitenesses", definitenesses)
        object.__setattr__(self, "states", states)
        object.__setattr__(self, "animacy", bool(animacies))
        object.__setattr__(self, "grammatical_number", bool(numbers))
        object.__setattr__(self, "noun_class", bool(noun_classes))
        object.__setattr__(self, "styles", _normalize_string_values(self.styles))
        object.__setattr__(
            self,
            "features",
            tuple(item if isinstance(item, FeatureSpec) else FeatureSpec(**item) for item in self.features),
        )
        if not isinstance(self.domain, NumericDomain):
            object.__setattr__(self, "domain", NumericDomain(**self.domain))


@dataclass(frozen=True, slots=True)
class LocaleCapabilities:
    """Renderer capabilities with exact profiles and compatibility summaries."""

    forms: frozenset[NumeralForm] = frozenset()
    syntaxes: frozenset[Syntax] = frozenset({Syntax.STANDALONE})
    genders: frozenset[Gender] = frozenset()
    cases: frozenset[str | Case] = frozenset()
    animacies: frozenset[str] = frozenset()
    grammatical_numbers: frozenset[str] = frozenset()
    noun_classes: frozenset[str] = frozenset()
    definitenesses: frozenset[str] = frozenset()
    states: frozenset[str] = frozenset()
    styles: frozenset[str] = frozenset({"default"})
    notes: tuple[str, ...] = field(default_factory=tuple)
    profiles: tuple[CapabilityProfile, ...] = ()
    # Compatibility summary fields retained for callers of the original API.
    animacy: bool = False
    grammatical_number: bool = False
    noun_class: bool = False

    def __post_init__(self) -> None:
        profiles = tuple(
            profile if isinstance(profile, CapabilityProfile) else CapabilityProfile(**profile)
            for profile in self.profiles
        )
        if profiles:
            object.__setattr__(self, "profiles", profiles)
            object.__setattr__(self, "forms", frozenset(profile.form for profile in profiles))
            object.__setattr__(self, "syntaxes", frozenset(s for p in profiles for s in p.syntaxes))
            object.__setattr__(self, "genders", frozenset(g for p in profiles for g in p.genders))
            object.__setattr__(self, "cases", frozenset(c for p in profiles for c in p.cases))
            object.__setattr__(self, "animacies", frozenset(a for p in profiles for a in p.animacies))
            object.__setattr__(self, "grammatical_numbers", frozenset(n for p in profiles for n in p.grammatical_numbers))
            object.__setattr__(self, "noun_classes", frozenset(n for p in profiles for n in p.noun_classes))
            object.__setattr__(self, "definitenesses", frozenset(d for p in profiles for d in p.definitenesses))
            object.__setattr__(self, "states", frozenset(s for p in profiles for s in p.states))
            object.__setattr__(self, "styles", frozenset(s for p in profiles for s in p.styles))
        else:
            forms = frozenset(NumeralForm.coerce(item) for item in self.forms)
            syntaxes = frozenset(Syntax.coerce(item) for item in self.syntaxes)
            genders = frozenset(Gender.coerce(item) for item in self.genders)
            cases = _normalize_open_values(self.cases)
            animacies = _normalize_string_values(self.animacies)
            numbers = _normalize_string_values(self.grammatical_numbers)
            noun_classes = _normalize_string_values(self.noun_classes)
            if self.animacy and not animacies:
                animacies = frozenset({"*"})
            if self.grammatical_number and not numbers:
                numbers = frozenset({"*"})
            if self.noun_class and not noun_classes:
                noun_classes = frozenset({"*"})
            profiles = tuple(
                CapabilityProfile(
                    form=form,
                    syntaxes=syntaxes,
                    genders=genders,
                    cases=cases,
                    animacies=animacies,
                    grammatical_numbers=numbers,
                    noun_classes=noun_classes,
                    definitenesses=self.definitenesses,
                    states=self.states,
                    styles=self.styles,
                )
                for form in sorted(forms, key=lambda item: item.value)
            )
            object.__setattr__(self, "profiles", profiles)
            object.__setattr__(self, "forms", forms)
            object.__setattr__(self, "syntaxes", syntaxes)
            object.__setattr__(self, "genders", genders)
            object.__setattr__(self, "cases", cases)
            object.__setattr__(self, "animacies", animacies)
            object.__setattr__(self, "grammatical_numbers", numbers)
            object.__setattr__(self, "noun_classes", noun_classes)
            object.__setattr__(self, "definitenesses", _normalize_string_values(self.definitenesses))
            object.__setattr__(self, "states", _normalize_string_values(self.states))
            object.__setattr__(self, "styles", _normalize_string_values(self.styles))
        object.__setattr__(self, "animacy", bool(self.animacies))
        object.__setattr__(self, "grammatical_number", bool(self.grammatical_numbers))
        object.__setattr__(self, "noun_class", bool(self.noun_classes))
