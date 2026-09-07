"""Generate the independent num2words compatibility corpus."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from numeralform.compat import num2words

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.validation.corpus import write_jsonl
    from tools.validation.model import (
        SerializedValue,
        ValidationCase,
        ValidationRequest,
    )
else:
    from .corpus import write_jsonl
    from .model import SerializedValue, ValidationCase, ValidationRequest


def generate(output: Path) -> None:
    cases = []
    for locale in ("en", "es", "ru"):
        for form in ("cardinal", "ordinal", "year"):
            for value in (0, 1, 2, 21, 42, 99, 100, 2024):
                try:
                    text = num2words(value, lang=locale, to=form)
                except Exception:  # noqa: BLE001, S112
                    continue
                request = ValidationRequest(
                    SerializedValue("int", value=str(value)), locale, form, "standalone"
                )
                cases.append(
                    ValidationCase(
                        f"num2words:{locale}:{form}:{value}",
                        request,
                        text,
                        source="num2words",
                    )
                )
    write_jsonl(output, cases)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests/validation/compatibility/num2words.jsonl"),
    )
    args = parser.parse_args(argv)
    generate(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
