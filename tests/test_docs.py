from __future__ import annotations

from pathlib import Path

from numeralform import __all__, capabilities, locales

ROOT = Path(__file__).parents[1]
MATRIX = ROOT / "docs" / "locales" / "capability-matrix.md"
API = ROOT / "docs" / "api.md"


def _matrix_rows() -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for line in MATRIX.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert len(cells) == 3, f"malformed capability-matrix row: {line!r}"
        locale_cell, forms, maxima = cells
        assert locale_cell.startswith("`") and locale_cell.endswith("`")
        locale = locale_cell[1:-1]
        assert locale not in rows, f"duplicate capability-matrix locale: {locale}"
        rows[locale] = (forms, maxima)
    return rows


def test_capability_matrix_matches_runtime():
    expected: dict[str, tuple[str, str]] = {}
    for locale in locales():
        locale_capabilities = capabilities(locale)
        profile_data = locale_capabilities.profiles
        forms = ", ".join(sorted(form.value for form in locale_capabilities.forms))
        maxima = sorted(
            {
                profile.domain.maximum
                for profile in profile_data
                if profile.domain.maximum is not None
            }
        )
        rendered_maxima = ", ".join(f"{maximum:,}" for maximum in maxima) or "unbounded"
        expected[locale] = (forms, rendered_maxima)
    assert _matrix_rows() == expected


def test_api_docs_name_intentionally_public_exports():
    documented = API.read_text(encoding="utf-8")
    for name in __all__:
        if name != "__version__":
            assert name in documented or name in {"Decimal", "Fraction"}


def test_documented_locale_parser_subset():
    documented = API.read_text(encoding="utf-8")
    assert "BCP-47-style" in documented
    assert "en-u-nu-latn" in documented
    assert "x-private" in documented
