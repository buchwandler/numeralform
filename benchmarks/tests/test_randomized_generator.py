from decimal import Decimal

from benchmarks.randomized.generator import generate_cases, shared_locales


def test_generation_is_seeded_and_filters_are_respected():
    kwargs = {
        "seed": 42,
        "count": 12,
        "canonical_locales": ("en", "de"),
        "external_locales": ("en", "de", "fr"),
        "locales": ("de",),
        "kinds": ("decimal",),
        "supports": lambda locale, kind, value: True,
        "currency_supports": lambda locale, value, currency: True,
    }
    first, _, _ = generate_cases(**kwargs)
    second, _, _ = generate_cases(**kwargs)
    assert first == second
    assert all(case.locale == "de" and case.kind == "decimal" for case in first)
    assert all(case.python_value() == Decimal(case.value.value) for case in first)


def test_shared_locales_normalizes_regional_spellings():
    assert shared_locales(canonical_locales=("en-IN", "de"), external_locales=("en_IN", "de")) == (
        "de",
        "en-IN",
    )
