from __future__ import annotations

from pathlib import Path

from numeralform import __all__, capabilities, locales

ROOT = Path(__file__).parents[1]
MATRIX = ROOT / "docs" / "locales" / "capability-matrix.md"
API = ROOT / "docs" / "api.md"


def _matrix_rows() -> set[str]:
    return {line for line in MATRIX.read_text().splitlines() if line.startswith("| `")}


def test_capability_matrix_matches_runtime():
    expected = set()
    for locale in locales():
        profile_data = capabilities(locale).profiles
        forms = ", ".join(sorted(form.value for form in capabilities(locale).forms))
        maxima = sorted(
            {
                profile.domain.maximum
                for profile in profile_data
                if profile.domain.maximum is not None
            }
        )
        rendered_maxima = ", ".join(f"{maximum:,}" for maximum in maxima) or "unbounded"
        expected.add(f"| `{locale}` | {forms} | {rendered_maxima} |")
    assert _matrix_rows() == expected


def test_api_docs_name_intentionally_public_exports():
    documented = API.read_text()
    for name in __all__:
        if name != "__version__":
            assert name in documented or name in {"Decimal", "Fraction"}


def test_documented_locale_parser_subset():
    documented = API.read_text()
    assert "BCP-47-style" in documented
    assert "en-u-nu-latn" in documented
    assert "x-private" in documented
