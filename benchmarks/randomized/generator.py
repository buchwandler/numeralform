"""Deterministic semantic case generation for the randomized benchmark."""

from __future__ import annotations

import hashlib
import random
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import tomllib

import numeralform
from benchmarks.validation.oracle.num2words import oracle_locales
from numeralform import render_currency

from .model import CASE_KINDS, RandomCase, SerializedRandomValue
from .surfaces import surface_for

BENCHMARK_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = BENCHMARK_ROOT / "config" / "num2words_random.toml"
SCHEMA_VERSION = 1
GENERATOR_VERSION = 1


@dataclass(frozen=True, slots=True)
class RandomConfig:
    raw: dict
    profile: str

    @property
    def randomized(self) -> dict:
        return self.raw["randomized"]

    @property
    def weights(self) -> dict[str, int]:
        return dict(self.randomized["weights"])

    @property
    def values(self) -> dict:
        return self.randomized[self.profile]

    @property
    def config_hash(self) -> str:
        import json

        encoded = json.dumps(self.raw, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


def load_config(path: Path = CONFIG_PATH, profile: str | None = None) -> RandomConfig:
    with path.open("rb") as stream:
        raw = tomllib.load(stream)
    randomized = raw.get("randomized")
    if not isinstance(randomized, dict):
        raise TypeError("randomized configuration requires [randomized]")
    selected = profile or randomized.get("default_profile")
    if selected not in {"common", "stress"}:
        raise ValueError(f"unknown randomized profile: {selected!r}")
    required = {"schema_version", "generator_version", "weights", selected}
    missing = required - set(randomized)
    if missing:
        raise ValueError("randomized configuration missing: " + ", ".join(sorted(missing)))
    if randomized["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported randomized schema version")
    if randomized["generator_version"] != GENERATOR_VERSION:
        raise ValueError("unsupported randomized generator version")
    weights = randomized["weights"]
    if tuple(weights) != CASE_KINDS or any(not isinstance(v, int) or v <= 0 for v in weights.values()):
        raise ValueError("randomized weights must list each case kind in stable order")
    if not isinstance(randomized[selected], dict):
        raise TypeError(f"randomized profile {selected!r} must be a table")
    return RandomConfig(raw, selected)


def normalize_locale(locale: str) -> str:
    return locale.replace("_", "-")


def shared_locales(
    oracle_root: Path | None = None,
    *,
    canonical_locales: Iterable[str] | None = None,
    external_locales: Iterable[str] | None = None,
) -> tuple[str, ...]:
    canonical = set(canonical_locales or numeralform.locales())
    if external_locales is None:
        if oracle_root is None:
            raise RuntimeError("a verified oracle checkout is required for locale discovery")
        external = set(oracle_locales(oracle_root))
    else:
        external = {normalize_locale(locale) for locale in external_locales}
    return tuple(sorted(canonical & external))


def weighted_choice(rng: random.Random, weights: dict[str, int]) -> str:
    total = sum(weights.values())
    point = rng.randrange(total)
    for key, weight in weights.items():
        if point < weight:
            return key
        point -= weight
    raise AssertionError("weighted choice exhausted")


def random_integer(
    rng: random.Random,
    *,
    minimum: int,
    maximum: int,
    edge_values: Iterable[int],
    edge_probability: float,
) -> int:
    if rng.random() < edge_probability:
        candidates = [value for value in edge_values if minimum <= value <= maximum]
        if candidates:
            return rng.choice(candidates)
    return rng.randint(minimum, maximum)


def _edge_values() -> tuple[int, ...]:
    return (
        0,
        1,
        2,
        3,
        9,
        10,
        11,
        19,
        20,
        21,
        29,
        30,
        31,
        99,
        100,
        101,
        199,
        200,
        201,
        999,
        1000,
        1001,
        1999,
        2000,
        2001,
        9999,
        10000,
        10001,
        99999,
        100000,
        100001,
        999999,
        1000000,
        1000001,
    )


def _decimal(rng: random.Random, profile: dict) -> Decimal:
    integer = rng.randint(0, int(profile["decimal_integer_max"]))
    digits = rng.choice(tuple(int(value) for value in profile["decimal_fraction_digits"]))
    fraction = rng.randrange(10**digits)
    return Decimal(f"{integer}.{fraction:0{digits}d}")


def _currency_decimal(rng: random.Random, profile: dict) -> Decimal:
    minimum = Decimal(str(profile["currency_min"]))
    maximum = Decimal(str(profile["currency_max"]))
    digits = max(-minimum.as_tuple().exponent, -maximum.as_tuple().exponent)
    lower = int(minimum * (10**digits))
    upper = int(maximum * (10**digits))
    return Decimal(rng.randint(lower, upper)) / (10**digits)
def _currency_decimal(rng: random.Random, profile: dict) -> Decimal:
    minimum = Decimal(str(profile["currency_min"]))
    maximum = Decimal(str(profile["currency_max"]))
    digits = max(-minimum.as_tuple().exponent, -maximum.as_tuple().exponent)
    scale = 10**digits
    lower = int(minimum * scale)
    upper = int(maximum * scale)
    scaled = rng.randint(lower, upper)
    integer, fraction = divmod(scaled, scale)
    return Decimal(f"{integer}.{fraction:0{digits}d}")
def _candidate(
    rng: random.Random,
    locale: str,
    kind: str,
    profile: dict,
    currency_choices: tuple[str, ...],
) -> tuple[int | Decimal, str | None]:
    edge_probability = float(profile.get("edge_probability", 0.0))
    if kind in {"cardinal", "ordinal", "year"}:
        if kind == "cardinal":
            minimum, maximum = int(profile["cardinal_min"]), int(profile["cardinal_max"])
            edges = _edge_values()
        elif kind == "ordinal":
            minimum, maximum = int(profile["ordinal_min"]), int(profile["ordinal_max"])
            edges = _edge_values()
        else:
            minimum, maximum = int(profile["year_min"]), int(profile["year_max"])
            edges = (1000, 1001, 1099, 1100, 1900, 1901, 1999, 2000, 2001, 2009, 2010, 2024, 2099)
        value = random_integer(
            rng,
            minimum=minimum,
            maximum=maximum,
            edge_values=edges,
            edge_probability=edge_probability,
        )
        if kind == "cardinal" and profile.get("cardinal_min", 0) < 0 and rng.random() < 0.1:
            value = -abs(value)
        return value, None
    if kind == "decimal":
        return _decimal(rng, profile), None
    if kind == "currency":
        return _currency_decimal(rng, profile), rng.choice(currency_choices)
    raise ValueError(f"unknown case kind: {kind!r}")

def _default_supports(locale: str, kind: str, value: int | Decimal) -> bool:
    if kind == "decimal":
        from numeralform import DecimalNumber

        return numeralform.supports(locale, form="decimal", value=DecimalNumber.from_decimal(value))
    return numeralform.supports(locale, form=kind, value=value)

def _default_currency_supports(locale: str, value: Decimal, currency: str) -> bool:
    try:
        render_currency(value, locale=locale, currency=currency)
    except Exception:  # noqa: BLE001
        return False
    return True


def generate_cases(
    *,
    seed: int,
    count: int,
    profile: str = "common",
    oracle_root: Path | None = None,
    locales: Iterable[str] | None = None,
    kinds: Iterable[str] | None = None,
    currencies: Iterable[str] | None = None,
    config_path: Path = CONFIG_PATH,
    canonical_locales: Iterable[str] | None = None,
    external_locales: Iterable[str] | None = None,
    supports: Callable[[str, str, int | Decimal], bool] | None = None,
    currency_supports: Callable[[str, Decimal, str], bool] | None = None,
) -> tuple[tuple[RandomCase, ...], dict[str, int], RandomConfig]:
    if count < 0:
        raise ValueError("case count must be non-negative")
    config = load_config(config_path, profile)
    available_locales = shared_locales(
        oracle_root,
        canonical_locales=canonical_locales,
        external_locales=external_locales,
    )
    selected_locales = tuple(sorted({normalize_locale(locale) for locale in locales or available_locales}))
    if not set(selected_locales) <= set(available_locales):
        unknown = sorted(set(selected_locales) - set(available_locales))
        raise ValueError("requested locales are not shared: " + ", ".join(unknown))
    selected_kinds = tuple(kinds or CASE_KINDS)
    if not selected_kinds or not set(selected_kinds) <= set(CASE_KINDS):
        raise ValueError("requested kinds must be selected from the supported case kinds")
    profile_values = config.values
    selected_currencies = tuple(currencies or profile_values["currencies"])
    if not selected_currencies:
        raise ValueError("at least one currency is required")
    rng = random.Random(seed)
    supports = supports or _default_supports
    currency_supports = currency_supports or _default_currency_supports
    generated: list[RandomCase] = []
    seen: set[tuple[str, str, str, str | None]] = set()
    rejected = {"generation_rejected_numeralform_unsupported": 0, "generation_rejected_duplicate": 0}
    max_attempts = max(count * int(profile_values.get("max_attempt_multiplier", 20)), count + 1)
    attempts = 0
    while len(generated) < count and attempts < max_attempts:
        attempts += 1
        locale = rng.choice(selected_locales)
        kind = weighted_choice(rng, {key: config.weights[key] for key in selected_kinds})
        value, currency = _candidate(rng, locale, kind, profile_values, selected_currencies)
        if profile == "common":
            supported = (
                currency_supports(locale, value, currency) if kind == "currency" else supports(locale, kind, value)
            )
            if not supported:
                rejected["generation_rejected_numeralform_unsupported"] += 1
                continue
        serialized = SerializedRandomValue.from_python(value)
        identity = (locale, kind, serialized.value, currency)
        if profile == "common" and identity in seen:
            rejected["generation_rejected_duplicate"] += 1
            continue
        seen.add(identity)
        surface, tags = surface_for(locale, kind, value, currency=currency, rng=rng)
        generated.append(
            RandomCase(
                SCHEMA_VERSION,
                GENERATOR_VERSION,
                seed,
                len(generated),
                f"random-v1:{seed}:{len(generated):06d}",
                locale,
                kind,
                surface,
                serialized,
                currency,
                tags,
            )
        )
    if len(generated) != count:
        raise RuntimeError(
            f"unable to generate {count} supported unique cases after {attempts} attempts"
        )
    return tuple(generated), rejected, config


__all__ = [
    "CONFIG_PATH",
    "GENERATOR_VERSION",
    "RandomConfig",
    "generate_cases",
    "load_config",
    "normalize_locale",
    "random_integer",
    "shared_locales",
    "weighted_choice",
]
