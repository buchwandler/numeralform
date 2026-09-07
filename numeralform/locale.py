"""Locale parsing, canonicalization, and capability declarations."""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from .errors import InvalidRequestError
from .model import Animacy, Case, Gender, NumeralForm, Syntax


_LOCALE_RE = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{2,8})*$")
_ALIASES = {"jp": "ja", "cn": "zh-CN"}


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
class LocaleCapabilities:
    forms: frozenset[NumeralForm]
    syntaxes: frozenset[Syntax] = frozenset({Syntax.STANDALONE})
    genders: frozenset[Gender] = frozenset()
    cases: frozenset[Case] = frozenset()
    animacy: bool = False
    grammatical_number: bool = False
    noun_class: bool = False
    styles: frozenset[str] = frozenset({"default"})
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "forms", frozenset(NumeralForm.coerce(item) for item in self.forms)
        )
        object.__setattr__(
            self, "syntaxes", frozenset(Syntax.coerce(item) for item in self.syntaxes)
        )
        object.__setattr__(
            self, "genders", frozenset(Gender.coerce(item) for item in self.genders)
        )
        object.__setattr__(
            self, "cases", frozenset(Case.coerce(item) for item in self.cases)
        )
        object.__setattr__(self, "styles", frozenset(self.styles))
