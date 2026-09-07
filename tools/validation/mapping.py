"""Explicit validation mappings loaded from validation.toml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import tomllib

from numeralform import capabilities


@dataclass(frozen=True, slots=True)
class Mapping:
    id: str
    numeralform_locale: str
    form: str
    syntax: str
    style: str
    oracle: str
    oracle_locale: str | None = None
    rule_set: str | None = None
    mode: str = "strict"

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Mapping:
        fields = {
            key: data[key]
            for key in (
                "id",
                "numeralform_locale",
                "form",
                "syntax",
                "style",
                "oracle",
                "oracle_locale",
                "rule_set",
                "mode",
            )
            if key in data
        }
        mapping = cls(**fields)
        if not mapping.id or mapping.mode not in {"strict", "reviewed-only"}:
            raise ValueError(f"invalid mapping {mapping.id!r}")
        return mapping


def load_config(path: Path) -> dict[str, object]:
    with path.open("rb") as stream:
        config = tomllib.load(stream)
    mappings = config.get("mapping", [])
    if not isinstance(mappings, list):
        raise ValueError("mapping must be an array of tables")  # noqa: TRY004
    seen: set[str] = set()
    parsed: list[Mapping] = []
    for data in mappings:
        mapping = Mapping.from_dict(data)
        if mapping.id in seen:
            raise ValueError(f"duplicate mapping ID: {mapping.id}")
        seen.add(mapping.id)
        validate_mapping(mapping)
        parsed.append(mapping)
    config["_mappings"] = tuple(parsed)
    return config


def mappings(config: dict[str, object]) -> tuple[Mapping, ...]:
    return tuple(config.get("_mappings", ()))


def validate_mapping(mapping: Mapping) -> None:
    caps = capabilities(mapping.numeralform_locale)
    form = mapping.form
    syntax = mapping.syntax
    if not any(profile.form.value == form for profile in caps.profiles):
        raise ValueError(f"mapping {mapping.id}: unsupported form {form!r}")
    matching = [profile for profile in caps.profiles if profile.form.value == form]
    if not any(
        syntax in {item.value for item in profile.syntaxes} for profile in matching
    ):
        raise ValueError(f"mapping {mapping.id}: unsupported syntax {syntax!r}")
    if not any(
        mapping.style in profile.styles
        for profile in matching
        if syntax in {item.value for item in profile.syntaxes}
    ):
        raise ValueError(f"mapping {mapping.id}: unsupported style {mapping.style!r}")
    if mapping.mode == "strict" and (not mapping.oracle or not mapping.rule_set):
        raise ValueError(
            f"mapping {mapping.id}: strict mappings require oracle and explicit rule_set"
        )


def mapping_by_id(config: dict[str, object], mapping_id: str) -> Mapping:
    for mapping in mappings(config):
        if mapping.id == mapping_id:
            return mapping
    raise KeyError(mapping_id)
