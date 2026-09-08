"""Generate deterministic compatibility data from a pinned external oracle.

This maintainer-only tool never imports Numeralform's adapter while generating
expected values.  Generated cases target ``compat:num2words-0.5.14`` and can be
checked offline after the oracle data has been committed.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
import tempfile
import unicodedata
from decimal import Decimal
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.validation.corpus import file_sha256, write_jsonl
    from tools.validation.model import (
        CompatInvocation,
        SerializedCompatValue,
        ValidationCase,
    )
else:
    from .corpus import file_sha256, write_jsonl
    from .model import CompatInvocation, SerializedCompatValue, ValidationCase


CONFIG_PATH = Path("compatibility.toml")
ORACLE_PACKAGE = "num2words"
PINNED_ORACLE_VERSION = "0.5.14"
PINNED_ORACLE_COMMIT = "07814cb114157f582c40a00119c2e9faba8dcee2"
UPSTREAM_LOCALES = (
    "am",
    "ar",
    "az",
    "be",
    "bn",
    "ca",
    "ce",
    "cs",
    "cy",
    "da",
    "de",
    "en",
    "en-IN",
    "en-NG",
    "eo",
    "es",
    "es-CO",
    "es-CR",
    "es-GT",
    "es-NI",
    "es-VE",
    "fa",
    "fi",
    "fr",
    "fr-BE",
    "fr-CH",
    "fr-DZ",
    "he",
    "hi",
    "hu",
    "hy",
    "id",
    "is",
    "it",
    "ja",
    "kn",
    "ko",
    "kz",
    "lt",
    "lv",
    "mn",
    "nl",
    "no",
    "pl",
    "pt",
    "pt-BR",
    "ro",
    "ru",
    "sk",
    "sl",
    "sr",
    "sv",
    "te",
    "tet",
    "tg",
    "th",
    "tr",
    "uk",
    "vi",
    "zh",
    "zh-CN",
    "zh-HK",
    "zh-TW",
)
DEFAULT_VALUES = (0, 1, 2, 3, 10, 11, 19, 20, 21, 42, 99, 100, 101, 999, 1000, 2024)
FORMS = ("cardinal", "ordinal", "ordinal_num", "year", "currency")


def _load_toml(path: Path) -> dict[str, Any]:
    import tomllib

    with path.open("rb") as stream:
        data = tomllib.load(stream)
    try:
        config = data["compat"]["num2words"]
    except (KeyError, TypeError) as exc:
        raise ValueError("compatibility config requires [compat.num2words]") from exc
    if not isinstance(config, dict):
        raise ValueError("num2words compatibility config must be a table")  # noqa: TRY004
    required = {
        "repository",
        "commit",
        "version",
        "locales",
        "forms",
        "profiles",
        "values",
    }
    missing = required - set(config)
    if missing:
        raise ValueError("compatibility config missing: " + ", ".join(sorted(missing)))
    if (
        config["commit"] != PINNED_ORACLE_COMMIT
        or config["version"] != PINNED_ORACLE_VERSION
    ):
        raise ValueError("compatibility config does not identify the pinned oracle")
    if tuple(config["locales"]) != UPSTREAM_LOCALES:
        raise ValueError(
            "compatibility config locales must match the pinned 63-locale scope"
        )
    return config


def _external_num2words():
    """Load the external oracle, never the Numeralform compatibility adapter."""
    from num2words import (
        num2words as external_num2words,  # type: ignore[import-not-found]
    )

    return external_num2words


def _oracle_version() -> str:
    return importlib.metadata.version(ORACLE_PACKAGE)


def _value(value: object) -> SerializedCompatValue:
    return SerializedCompatValue.from_python(value)


def _invocations(
    locales: tuple[str, ...],
    values: tuple[int, ...],
    forms: tuple[str, ...],
    profiles: tuple[str, ...],
):
    for locale in locales:
        if "integer" in profiles:
            for form in forms:
                for value in values:
                    yield (
                        locale,
                        form,
                        CompatInvocation(
                            "num2words",
                            (_value(value),),
                            {"lang": _value(locale), "to": _value(form)},
                        ),
                    )
        if "decimal" in profiles:
            for value in (0.0, 0.01, -0.01, 1.2, 12.5, 123.4):
                yield (
                    locale,
                    "cardinal",
                    CompatInvocation(
                        "num2words", (_value(value),), {"lang": _value(locale)}
                    ),
                )
            for value in (Decimal("1.20"), Decimal("2.995")):
                yield (
                    locale,
                    "cardinal",
                    CompatInvocation(
                        "num2words", (_value(value),), {"lang": _value(locale)}
                    ),
                )
        if "string" in profiles:
            for value in ("1.20", "1e3", "-0.01"):
                yield (
                    locale,
                    "cardinal",
                    CompatInvocation(
                        "num2words", (_value(value),), {"lang": _value(locale)}
                    ),
                )
        if "currency" in profiles and "currency" in forms:
            for value in (0, 1, 5, 99, 100, 101, 1234, 2.995, Decimal("2.995"), "1.20"):
                for cents in (True, False):
                    yield (
                        locale,
                        "currency",
                        CompatInvocation(
                            "num2words",
                            (_value(value),),
                            {
                                "lang": _value(locale),
                                "to": _value("currency"),
                                "cents": _value(cents),
                            },
                        ),
                    )
        if "errors" in profiles:
            yield (
                locale,
                "ordinal_num",
                CompatInvocation(
                    "num2words",
                    (_value(-1),),
                    {"lang": _value(locale), "to": _value("ordinal_num")},
                ),
            )
            yield (
                locale,
                "cardinal",
                CompatInvocation(
                    "num2words", (_value(True),), {"lang": _value(locale)}
                ),
            )


def generate_cases(
    *,
    config_path: Path = CONFIG_PATH,
    locales: tuple[str, ...] | None = None,
    values: tuple[int, ...] | None = None,
) -> list[ValidationCase]:
    config = _load_toml(config_path)
    selected_locales = locales or tuple(config["locales"])
    selected_values = values or tuple(config["values"])
    forms = tuple(config["forms"])
    profiles = tuple(config["profiles"])
    version = _oracle_version()
    if version != PINNED_ORACLE_VERSION:
        raise RuntimeError(
            f"unsupported oracle version {version!r}; expected {PINNED_ORACLE_VERSION!r}"
        )
    external_num2words = _external_num2words()
    cases: list[ValidationCase] = []
    for locale, form, invocation in _invocations(
        selected_locales, selected_values, forms, profiles
    ):
        _, positional, kwargs = invocation.as_python()
        try:
            text = unicodedata.normalize(
                "NFC", str(external_num2words(*positional, **kwargs))
            )
        except Exception as exc:  # noqa: BLE001
            cases.append(
                ValidationCase(
                    f"num2words-{version}:{locale}:{form}:error:{len(cases)}",
                    None,
                    "",
                    mapping="external-num2words",
                    oracle={
                        "package": ORACLE_PACKAGE,
                        "version": version,
                        "commit": PINNED_ORACLE_COMMIT,
                    },
                    source="external-num2words",
                    target="compat:num2words-0.5.14",
                    invocation=invocation,
                    expected_exception_type=type(exc).__name__,
                )
            )
        else:
            cases.append(
                ValidationCase(
                    f"num2words-{version}:{locale}:{form}:{len(cases)}",
                    None,
                    text,
                    mapping="external-num2words",
                    oracle={
                        "package": ORACLE_PACKAGE,
                        "version": version,
                        "commit": PINNED_ORACLE_COMMIT,
                    },
                    source="external-num2words",
                    target="compat:num2words-0.5.14",
                    invocation=invocation,
                )
            )
    return cases


def _manifest(
    output: Path,
    cases: list[ValidationCase],
    config_path: Path,
    config: dict[str, Any],
) -> dict[str, object]:
    return {
        "schema_version": 3,
        "source": {
            "kind": "github-revision",
            "repository": config["repository"],
            "commit": config["commit"],
            "package": ORACLE_PACKAGE,
            "version": config["version"],
            "locales": list(config["locales"]),
            "forms": list(config["forms"]),
            "profiles": list(config["profiles"]),
        },
        "normalization": "NFC",
        "config": str(config_path),
        "config_sha256": file_sha256(config_path),
        "generated_by": "tools/validation/generate_num2words.py",
        "files": {output.name: {"cases": len(cases), "sha256": file_sha256(output)}},
    }


def generate(
    output: Path, *, config_path: Path = CONFIG_PATH, check: bool = False
) -> Path:
    config = _load_toml(config_path)
    cases = generate_cases(config_path=config_path)
    if check:
        with tempfile.TemporaryDirectory() as directory:
            temporary_output = Path(directory) / output.name
            write_jsonl(temporary_output, cases)
            expected_manifest = _manifest(temporary_output, cases, config_path, config)
            if (
                not output.is_file()
                or output.read_bytes() != temporary_output.read_bytes()
            ):
                raise RuntimeError(f"compatibility corpus is stale: {output}")
            manifest_path = output.parent / "manifest.json"
            if (
                not manifest_path.is_file()
                or json.loads(manifest_path.read_text()) != expected_manifest
            ):
                raise RuntimeError(f"compatibility manifest is stale: {manifest_path}")
        return output.parent / "manifest.json"
    write_jsonl(output, cases)
    manifest_path = output.parent / "manifest.json"
    manifest = _manifest(output, cases, config_path, config)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests/validation/compatibility/num2words-0.5.14.jsonl"),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify committed corpus and manifest without writing",
    )
    args = parser.parse_args(argv)
    manifest = generate(args.output, config_path=args.config, check=args.check)
    print(
        f"{'checked' if args.check else 'wrote'} external compatibility corpus and manifest: {args.output}, {manifest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
