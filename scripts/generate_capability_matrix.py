from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

OUTPUT = ROOT / "docs" / "locales" / "capability-matrix.md"

PREAMBLE = """<!-- Generated from numeralform.capabilities(); do not edit by hand. -->

# Runtime capability matrix

This matrix is generated from the executable capability profiles. It summarizes the
forms and maximum integer domains advertised by each canonical locale. The
profiles returned by `capabilities(locale)` remain authoritative for exact syntax,
morphology, style, and feature constraints.

"""


def _rows() -> list[tuple[str, str, str]]:
    from numeralform import capabilities, locales

    rows: list[tuple[str, str, str]] = []
    for locale in locales():
        locale_capabilities = capabilities(locale)
        forms = ", ".join(sorted(form.value for form in locale_capabilities.forms))
        maxima = sorted(
            {
                profile.domain.maximum
                for profile in locale_capabilities.profiles
                if profile.domain.maximum is not None
            }
        )
        rendered_maxima = ", ".join(f"{maximum:,}" for maximum in maxima) or "unbounded"
        rows.append((f"`{locale}`", forms, rendered_maxima))
    return rows


def _table(rows: list[tuple[str, str, str]]) -> str:
    headers = ("Locale", "Reviewed forms", "Advertised integer maximums")
    all_rows = [headers, *rows]
    widths = [max(len(row[index]) for row in all_rows) for index in range(3)]

    def render_row(row: tuple[str, str, str]) -> str:
        return (
            "| "
            + " | ".join(f"{row[index]:<{widths[index]}}" for index in range(3))
            + " |"
        )

    separator = "| " + " | ".join("-" * width for width in widths) + " |"
    return "\n".join(
        [render_row(headers), separator, *(render_row(row) for row in rows)]
    )


def render() -> str:
    return PREAMBLE + _table(_rows()) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the checked-in capability matrix is stale.",
    )
    args = parser.parse_args()

    generated = render()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8")
        if current != generated:
            print(
                "docs/locales/capability-matrix.md is stale; "
                "run: python scripts/generate_capability_matrix.py"
            )
            return 1
        return 0

    OUTPUT.write_text(generated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
