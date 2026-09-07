"""Generate deterministic frozen corpora from the pinned ICU oracle."""

from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path

if __package__ in {None, ""}:  # support the documented ``python tools/...py`` form
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.validation.cases import case_id, deterministic_values
    from tools.validation.corpus import manifest_for, write_jsonl, write_manifest
    from tools.validation.mapping import Mapping, load_config, mappings
    from tools.validation.model import (
        SerializedValue,
        ValidationCase,
        ValidationRequest,
    )
    from tools.validation.normalize import normalize_nfc
    from tools.validation.oracle.icu import ICUOracle, OracleUnavailable
else:
    from .cases import case_id, deterministic_values
    from .corpus import manifest_for, write_jsonl, write_manifest
    from .mapping import Mapping, load_config, mappings
    from .model import SerializedValue, ValidationCase, ValidationRequest
    from .normalize import normalize_nfc
    from .oracle.icu import ICUOracle, OracleUnavailable


def config_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_mapping(
    mapping: Mapping, config: dict[str, object], oracle: ICUOracle
) -> list[ValidationCase]:
    coverage = config["coverage"]
    maximum = int(coverage.get("exhaustive_max", 9999))
    values = deterministic_values(
        int(coverage.get("exhaustive_min", 0)),
        maximum,
        seed=int(coverage.get("random_seed", 0)),
        per_magnitude=int(coverage.get("random_per_magnitude", 0)),
        boundary_radius=int(coverage.get("boundary_radius", 3)),
    )
    negative = range(-999, 0) if mapping.numeralform_locale == "en" else range(-99, 0)
    values = sorted(set(values).union(negative))
    cases: list[ValidationCase] = []
    for value in values:
        expected = normalize_nfc(
            oracle.format(
                value,
                locale=mapping.oracle_locale or mapping.numeralform_locale,
                rule_set=mapping.rule_set or "",
            )
        )
        request = ValidationRequest(
            SerializedValue("int", value=str(value)),
            mapping.numeralform_locale,
            mapping.form,
            mapping.syntax,
            None if mapping.style == "default" else mapping.style,
        )
        cases.append(
            ValidationCase(
                case_id(mapping.id, "int", value),
                request,
                expected,
                mapping=mapping.id,
                oracle={
                    "locale": mapping.oracle_locale or mapping.numeralform_locale,
                    "rule_set": mapping.rule_set or "",
                },
                source="icu-rbnf",
            )
        )
    return cases


def generate(
    config_path: Path,
    output: Path,
    selected: set[str] | None = None,
    *,
    allow_oracle_version: bool = False,
) -> None:
    config = load_config(config_path)
    oracle = ICUOracle()
    info = oracle.info()
    expected_release = str(config["cldr"]["release"])
    if not allow_oracle_version and info.cldr_version not in {
        expected_release,
        f"CLDR {expected_release}",
    }:
        raise RuntimeError(
            f"oracle CLDR version {info.cldr_version!r} does not match pinned {expected_release!r}; use --allow-oracle-version only for explicit review"
        )
    for mapping in mappings(config):
        if selected and mapping.id not in selected:
            continue
        if mapping.mode == "strict":
            available = oracle.list_rule_sets(
                mapping.oracle_locale or mapping.numeralform_locale
            )
            if mapping.rule_set not in available:
                raise RuntimeError(
                    f"mapping {mapping.id} requests unavailable rule set {mapping.rule_set!r}; available: {', '.join(available)}"
                )
    output.mkdir(parents=True, exist_ok=True)
    for mapping in mappings(config):
        if (selected and mapping.id not in selected) or mapping.mode != "strict":
            continue
        cases = generate_mapping(mapping, config, oracle)
        write_jsonl(output / f"{mapping.numeralform_locale}.jsonl", cases)
    manifest = manifest_for(
        output,
        source={
            "kind": "icu-rbnf",
            "cldr_version": expected_release,
            "icu_version": info.implementation_version,
            "unicode_version": info.unicode_version,
        },
        config_sha256=config_hash(config_path),
    )
    write_manifest(output / "manifest.json", manifest)


def check(
    config_path: Path,
    output: Path,
    selected: set[str] | None,
    allow_oracle_version: bool,
) -> int:
    with tempfile.TemporaryDirectory() as directory:
        generated = Path(directory) / "cldr"
        generate(
            config_path, generated, selected, allow_oracle_version=allow_oracle_version
        )
        expected = sorted(path for path in generated.glob("*") if path.is_file())
        actual = sorted(path for path in output.glob("*") if path.is_file())
        if [path.name for path in expected] != [path.name for path in actual]:
            print("CLDR corpus drift: file sets differ")
            return 1
        for source, target in zip(expected, actual):
            if source.read_bytes() != target.read_bytes():
                print(f"CLDR corpus drift: {target}")
                return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("validation.toml"))
    parser.add_argument("--output", type=Path, default=Path("tests/validation/cldr"))
    parser.add_argument("--mapping", action="append", dest="mapping")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--list-rule-sets", metavar="LOCALE")
    parser.add_argument("--allow-oracle-version", action="store_true")
    args = parser.parse_args(argv)
    selected = set(args.mapping or ()) or None
    try:
        if args.list_rule_sets:
            oracle = ICUOracle()
            print("\n".join(oracle.list_rule_sets(args.list_rule_sets)))
            return 0
        if args.check:
            return check(args.config, args.output, selected, args.allow_oracle_version)
        generate(
            args.config,
            args.output,
            selected,
            allow_oracle_version=args.allow_oracle_version,
        )
    except OracleUnavailable as exc:
        print(f"ORACLE UNAVAILABLE: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"GENERATION ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
