"""Generate frozen compatibility data from the external ``num2words`` oracle.

This module is maintainer tooling only.  It must not import Numeralform's
compatibility adapter: doing so would make the expected data self-referential.
The generated corpus is safe to check offline after generation.
"""

from __future__ import annotations

import importlib.metadata
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.validation.corpus import file_sha256, write_jsonl
    from tools.validation.model import (
        SerializedValue,
        ValidationCase,
        ValidationRequest,
    )
else:
    from .corpus import file_sha256, write_jsonl
    from .model import SerializedValue, ValidationCase, ValidationRequest

ORACLE_PACKAGE = "num2words"
PINNED_ORACLE_VERSION = "0.5.14"
DEFAULT_LOCALES = ("en", "es", "ru")
DEFAULT_VALUES = (0, 1, 2, 3, 10, 11, 19, 20, 21, 42, 99, 100, 101, 999, 1000, 2024)
FORMS = ("cardinal", "ordinal", "year")


def _external_num2words():
    """Load the external oracle with an intentionally obvious import."""
    from num2words import num2words as external_num2words  # type: ignore[import-not-found]

    return external_num2words


def _oracle_version() -> str:
    return importlib.metadata.version(ORACLE_PACKAGE)


def generate_cases(
    *,
    locales: tuple[str, ...] = DEFAULT_LOCALES,
    values: tuple[int, ...] = DEFAULT_VALUES,
) -> list[ValidationCase]:
    version = _oracle_version()
    if version != PINNED_ORACLE_VERSION:
        raise RuntimeError(
            f"unsupported oracle version {version!r}; expected {PINNED_ORACLE_VERSION!r}"
        )
    external_num2words = _external_num2words()
    cases: list[ValidationCase] = []
    for locale in locales:
        for form in FORMS:
            for value in values:
                try:
                    text = str(external_num2words(value, lang=locale, to=form))
                except (NotImplementedError, TypeError, ValueError, KeyError):
                    continue
                request = ValidationRequest(
                    SerializedValue("int", value=str(value)), locale, form, "standalone"
                )
                cases.append(
                    ValidationCase(
                        f"num2words-{version}:{locale}:{form}:{value}",
                        request,
                        text,
                        mapping="external-num2words",
                        oracle={"package": ORACLE_PACKAGE, "version": version},
                        source="external-num2words",
                    )
                )
    return cases


def _manifest(
    output: Path, cases: list[ValidationCase], generator: str
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "source": {
            "kind": "external-package",
            "package": ORACLE_PACKAGE,
            "version": PINNED_ORACLE_VERSION,
            "locales": sorted({case.request.locale for case in cases}),
            "forms": sorted({case.request.form for case in cases}),
        },
        "normalization": "NFC",
        "generated_by": generator,
        "files": {output.name: {"cases": len(cases), "sha256": file_sha256(output)}},
    }


def generate(output: Path) -> Path:
    cases = generate_cases()
    write_jsonl(output, cases)
    manifest_path = output.parent / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            _manifest(output, cases, "tools/validation/generate_num2words.py"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests/validation/compatibility/num2words-0.5.14.jsonl"),
    )
    args = parser.parse_args(argv)
    manifest = generate(args.output)
    print(
        f"wrote external compatibility corpus and manifest: {args.output}, {manifest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
