"""Deterministic validation case generation."""

from __future__ import annotations

import random
from collections.abc import Iterable


def neighborhoods(
    thresholds: Iterable[int], minimum: int, maximum: int, radius: int = 3
) -> set[int]:
    result: set[int] = set()
    for threshold in thresholds:
        result.update(
            value
            for value in range(threshold - radius, threshold + radius + 1)
            if minimum <= value <= maximum
        )
    return result


def deterministic_values(
    minimum: int,
    maximum: int,
    *,
    seed: int,
    per_magnitude: int,
    boundary_radius: int = 3,
) -> list[int]:
    if minimum > maximum:
        return []
    values = set(range(maximum + 1)) if minimum == 0 and maximum <= 9999 else set()
    values.update(
        neighborhoods(
            (10, 20, 100, 1000, 1_000_000, 1_000_000_000),
            minimum,
            maximum,
            boundary_radius,
        )
    )
    probes = (
        19,
        20,
        21,
        29,
        30,
        31,
        39,
        40,
        41,
        89,
        90,
        91,
        99,
        100,
        101,
        109,
        110,
        111,
        119,
        120,
        121,
        199,
        200,
        201,
        999,
        1000,
        1001,
        999999,
        1000000,
        1000001,
        1001,
        1010,
        1011,
        1100,
        1101,
        1111,
        10001,
        10101,
        101001,
        1001001,
        21021,
        22022,
        25025,
    )
    values.update(value for value in probes if minimum <= value <= maximum)
    rng = random.Random(seed)
    magnitude = 1
    while magnitude <= maximum:
        upper = min(maximum, magnitude * 10 - 1)
        if upper >= max(minimum, magnitude):
            values.update(
                rng.randint(max(minimum, magnitude), upper)
                for _ in range(per_magnitude)
            )
        magnitude *= 10
    return sorted(values)


def case_id(mapping: str, kind: str, value: object) -> str:
    return f"{mapping}:{kind}:{value}"
