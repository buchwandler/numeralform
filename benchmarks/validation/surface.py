"""Pinned num2words call-surface discovery and classification."""

from __future__ import annotations

import hashlib
import inspect
import json
import tomllib
from pathlib import Path
from typing import Any

from .oracle.num2words import NUM2WORDS_COMMIT, oracle_module

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "num2words_surface.toml"


def discover_surface(root: Path) -> dict[str, dict[str, dict[str, Any]]]:
    module = oracle_module(root)
    converters = module.CONVERTER_CLASSES
    surface: dict[str, dict[str, dict[str, Any]]] = {}
    for locale, converter in sorted(converters.items()):
        forms: dict[str, dict[str, Any]] = {}
        for form in ("cardinal", "ordinal", "ordinal_num", "year", "currency"):
            method = getattr(converter, f"to_{form}", None)
            if method is None:
                continue
            signature = inspect.signature(method)
            forms[form] = {
                "parameters": {
                    name: {
                        "kind": parameter.kind.name,
                        "default": None if parameter.default is inspect.Parameter.empty else repr(parameter.default),
                    }
                    for name, parameter in signature.parameters.items()
                }
            }
        surface[str(locale).replace("_", "-")] = forms
    return surface


def load_surface_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with path.open("rb") as stream:
        return tomllib.load(stream)["surface"]


def unclassified_parameters(surface: dict[str, dict[str, dict[str, Any]]], config: dict[str, Any]) -> set[str]:
    ignored = set(config.get("value_parameters", ())) | {"self"}
    classifications = set(config.get("classifications", {}))
    discovered = {
        parameter
        for forms in surface.values()
        for details in forms.values()
        for parameter in details["parameters"]
        if parameter not in ignored
    }
    return discovered - classifications


def validate_surface(surface: dict[str, dict[str, dict[str, Any]]], config: dict[str, Any]) -> None:
    missing = unclassified_parameters(surface, config)
    if missing:
        raise ValueError("unclassified num2words parameters: " + ", ".join(sorted(missing)))
    invalid = set(config.get("classifications", {}).values()) - {
        "covered", "ignored-with-reason", "unsupported-by-numeralform", "oracle-internal", "free-form-sampled"
    }
    if invalid:
        raise ValueError("unknown surface classifications: " + ", ".join(sorted(invalid)))


def surface_manifest(root: Path, config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    surface = discover_surface(root)
    config = load_surface_config(config_path)
    validate_surface(surface, config)
    payload = json.dumps(surface, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": config["schema_version"],
        "oracle_commit": NUM2WORDS_COMMIT,
        "sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "locales": len(surface),
        "forms": sum(len(forms) for forms in surface.values()),
    }


__all__ = ["CONFIG_PATH", "discover_surface", "load_surface_config", "surface_manifest", "unclassified_parameters", "validate_surface"]
