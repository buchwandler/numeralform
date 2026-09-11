from pathlib import Path

from benchmarks.validation.surface import (
    discover_surface,
    load_surface_config,
    unclassified_parameters,
    validate_surface,
)

ORACLE_ROOT = Path(__file__).parents[1] / "data" / "oracles" / "num2words"


def test_pinned_surface_is_classified():
    surface = discover_surface(ORACLE_ROOT)
    config = load_surface_config()
    validate_surface(surface, config)
    assert len(surface) == 63
    assert unclassified_parameters(surface, config) == set()


def test_surface_inventory_contains_language_specific_parameters():
    surface = discover_surface(ORACLE_ROOT)
    assert "prefer" in surface["fi"]["cardinal"]["parameters"]
    assert "construct" in surface["he"]["cardinal"]["parameters"]
    assert "clazz" in surface["ce"]["cardinal"]["parameters"]
