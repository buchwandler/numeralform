"""Deterministic semantic case generation for the randomized benchmark."""

from __future__ import annotations

import hashlib
import json
import random
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import tomllib

import numeralform
from benchmarks.validation.oracle.num2words import oracle_locales
from numeralform import render_currency, supports_currency
from numeralform.compat._num2words.registry import LEGACY_CONVERTER_KEYS

from .model import CASE_KINDS, RandomCase, SerializedRandomValue
from .surfaces import surface_for

BENCHMARK_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = BENCHMARK_ROOT / "config" / "num2words_random.toml"
SCHEMA_VERSION = 3
GENERATOR_VERSION = 3


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
    def currency_variants(self) -> tuple[dict, ...]:
        return tuple(self.randomized.get("currency_variants", ()))

    @property
    def shared_exclusions(self) -> tuple[dict, ...]:
        return tuple(self.randomized.get("shared_exclusions", ()))

    @property
    def shared_option_support(self) -> dict:
        return dict(self.randomized.get("shared_option_support", {}))

    @property
    def shared_ordinal_zero_excluded_languages(self) -> frozenset[str]:
        return frozenset(
            self.randomized.get("shared_ordinal_zero_excluded_languages", ())
        )

    def currency_variants_for(self, locale: str) -> tuple[dict, ...]:
        variants = self.currency_variants
        if self.profile != "shared":
            return variants
        language = locale.split("-", 1)[0]
        currency_support = self.shared_option_support.get(language, {}).get(
            "currency", {}
        )
        allowed = currency_support.get("variants")
        if allowed is None:
            return variants
        allowed_ids = set(allowed)
        return tuple(
            variant for variant in variants if variant.get("id") in allowed_ids
        )

    @property
    def compat_variants(self) -> tuple[dict, ...]:
        return tuple(self.randomized.get("compat_variants", ()))

    @property
    def compat_transports(self) -> tuple[str, ...]:
        return tuple(self.randomized.get("compat_transports", ("native",)))

    @property
    def compat_call_variants(self) -> tuple[str, ...]:
        return tuple(self.randomized.get("compat_call_variants", ("to",)))

    @property
    def config_hash(self) -> str:
        encoded = json.dumps(self.raw, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


def load_config(path: Path = CONFIG_PATH, profile: str | None = None) -> RandomConfig:
    with path.open("rb") as stream:
        raw = tomllib.load(stream)
    randomized = raw.get("randomized")
    if not isinstance(randomized, dict):
        raise TypeError("randomized configuration requires [randomized]")
    selected = profile or randomized.get("default_profile")
    if selected not in {"shared", "numeralform", "common", "stress"}:
        raise ValueError(f"unknown randomized profile: {selected!r}")
    required = {"schema_version", "generator_version", "weights", selected}
    missing = required - set(randomized)
    if missing:
        raise ValueError(
            "randomized configuration missing: " + ", ".join(sorted(missing))
        )
    if randomized["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported randomized schema version")
    if randomized["generator_version"] != GENERATOR_VERSION:
        raise ValueError("unsupported randomized generator version")
    weights = randomized["weights"]
    if tuple(weights) != CASE_KINDS or any(
        not isinstance(v, int) or v <= 0 for v in weights.values()
    ):
        raise ValueError("randomized weights must list each case kind in stable order")
    if not isinstance(randomized[selected], dict):
        raise TypeError(f"randomized profile {selected!r} must be a table")
    return RandomConfig(raw, selected)


def normalize_locale(locale: str) -> str:
    return locale.replace("_", "-")


@dataclass(frozen=True, slots=True)
class SharedLocale:
    canonical: str
    oracle: str


_NUM2WORDS_CANONICAL_LOCALE_MAP = {"en": "en-GB"}


def shared_locale_pairs(
    oracle_root: Path | None = None,
    *,
    canonical_locales: Iterable[str] | None = None,
    external_locales: Iterable[str] | None = None,
) -> tuple[SharedLocale, ...]:
    canonical = {
        normalize_locale(locale)
        for locale in (canonical_locales or numeralform.locales())
    }
    if external_locales is None:
        if oracle_root is None:
            raise RuntimeError(
                "a verified oracle checkout is required for locale discovery"
            )
        external = {normalize_locale(locale) for locale in oracle_locales(oracle_root)}
    else:
        external = {normalize_locale(locale) for locale in external_locales}
    pairs: list[SharedLocale] = []
    for oracle in sorted(external):
        mapped = _NUM2WORDS_CANONICAL_LOCALE_MAP.get(oracle)
        if mapped in canonical:
            pairs.append(SharedLocale(mapped, oracle))
        elif oracle in canonical:
            pairs.append(SharedLocale(oracle, oracle))
    return tuple(pairs)


def compatibility_locale_pairs(
    oracle_root: Path | None = None,
    *,
    external_locales: Iterable[str] | None = None,
) -> tuple[SharedLocale, ...]:
    if external_locales is None:
        if oracle_root is None:
            raise RuntimeError(
                "a verified oracle checkout is required for locale discovery"
            )
        external = {normalize_locale(locale) for locale in oracle_locales(oracle_root)}
    else:
        external = {normalize_locale(locale) for locale in external_locales}
    supported = {normalize_locale(locale) for locale in LEGACY_CONVERTER_KEYS}
    return tuple(
        SharedLocale(locale, locale) for locale in sorted(external & supported)
    )


def shared_locales(
    oracle_root: Path | None = None,
    *,
    canonical_locales: Iterable[str] | None = None,
    external_locales: Iterable[str] | None = None,
) -> tuple[str, ...]:
    return tuple(
        pair.canonical
        for pair in shared_locale_pairs(
            oracle_root,
            canonical_locales=canonical_locales,
            external_locales=external_locales,
        )
    )


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


LOCALE_EDGE_VALUES: dict[str, tuple[int, ...]] = {
    "zh": (9, 10, 99, 100, 999, 1000, 9999, 10000, 100000000),
    "bn": (99, 100, 999, 1000, 99999, 100000),
    "hi": (99, 100, 999, 1000, 99999, 100000),
    "kn": (99, 100, 999, 1000, 99999, 100000),
    "te": (99, 100, 999, 1000, 99999, 100000),
}


def locale_edge_values(locale: str, kind: str = "cardinal") -> tuple[int, ...]:
    """Return reviewed locale boundaries for deterministic random probing."""
    if kind not in {"cardinal", "ordinal", "year"}:
        return ()
    return LOCALE_EDGE_VALUES.get(locale.split("-", 1)[0], ())


def _edge_values() -> tuple[int, ...]:
    return (
        0,
        1,
        2,
        3,
        4,
        9,
        10,
        11,
        12,
        13,
        19,
        20,
        21,
        22,
        23,
        29,
        30,
        31,
        32,
        33,
        99,
        100,
        101,
        102,
        103,
        109,
        110,
        111,
        112,
        113,
        119,
        120,
        121,
        122,
        123,
        199,
        200,
        201,
        999,
        1000,
        1001,
        1002,
        1003,
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


def _ordinal_edge_values() -> tuple[int, ...]:
    return (
        0,
        1,
        2,
        3,
        4,
        9,
        10,
        11,
        12,
        13,
        19,
        20,
        21,
        22,
        23,
        29,
        30,
        31,
        32,
        33,
        99,
        100,
        101,
        102,
        103,
        109,
        110,
        111,
        112,
        113,
        119,
        120,
        121,
        122,
        123,
        199,
        200,
        201,
        999,
        1000,
        1001,
        1002,
        1003,
        9999,
    )


def _year_edge_values() -> tuple[int, ...]:
    return (
        0,
        1,
        9,
        10,
        11,
        50,
        99,
        100,
        101,
        599,
        600,
        601,
        899,
        900,
        905,
        999,
        1000,
        1001,
        1009,
        1010,
        1099,
        1100,
        1101,
        1899,
        1900,
        1901,
        1909,
        1910,
        1999,
        2000,
        2001,
        2009,
        2010,
        2024,
        2099,
        2100,
        2101,
        2999,
        3000,
        3001,
        5555,
        6600,
        9999,
    )


def _decimal_edge_values() -> tuple[Decimal, ...]:
    return tuple(
        Decimal(value)
        for value in (
            "0.0",
            "0.00",
            "0.01",
            "0.001",
            "0.10",
            "0.20",
            "1.0",
            "1.00",
            "1.01",
            "1.10",
            "1.20",
            "9.99",
            "10.01",
            "10.10",
            "99.99",
            "100.01",
            "1000.01",
        )
    )


def _currency_edge_values(minor_units: int) -> tuple[Decimal, ...]:
    if minor_units == 0:
        return tuple(
            Decimal(value)
            for value in (
                "0",
                "1",
                "2",
                "4",
                "5",
                "10",
                "11",
                "12",
                "14",
                "20",
                "21",
                "22",
                "99",
                "100",
                "101",
            )
        )
    return tuple(
        Decimal(value)
        for value in (
            "0.00",
            "0.01",
            "0.02",
            "0.04",
            "0.05",
            "0.10",
            "0.11",
            "0.12",
            "0.14",
            "0.20",
            "0.21",
            "0.22",
            "0.99",
            "1.00",
            "1.01",
            "1.02",
            "1.11",
            "2.00",
            "2.01",
            "4.01",
            "5.01",
            "10.00",
            "11.00",
            "12.00",
            "14.00",
            "20.00",
            "21.00",
            "22.00",
            "101.01",
        )
    )


def _maybe_negative(
    rng: random.Random, value: int | Decimal, probability: float
) -> int | Decimal:
    if value == 0:
        return value
    return -value if rng.random() < probability else value


def _decimal(rng: random.Random, profile: dict) -> Decimal:
    if rng.random() < float(profile.get("edge_probability", 0.0)):
        value = rng.choice(_decimal_edge_values())
    else:
        integer = rng.randint(0, int(profile["decimal_integer_max"]))
        digits = rng.choice(
            tuple(int(value) for value in profile["decimal_fraction_digits"])
        )
        fraction = rng.randrange(10**digits)
        value = Decimal(f"{integer}.{fraction:0{digits}d}")
    return _maybe_negative(
        rng,
        value,
        float(
            profile.get(
                "decimal_negative_probability", profile.get("negative_probability", 0.0)
            )
        ),
    )


def _currency_decimal(rng: random.Random, profile: dict, currency: str) -> Decimal:
    minimum = Decimal(str(profile["currency_min"]))
    maximum = Decimal(str(profile["currency_max"]))
    digits = int(profile["currency_minor_units"][currency])
    if rng.random() < float(
        profile.get("currency_edge_probability", profile.get("edge_probability", 0.0))
    ):
        candidates = [
            value
            for value in _currency_edge_values(digits)
            if minimum <= value <= maximum
        ]
        value = rng.choice(candidates) if candidates else minimum
    else:
        scale = 10**digits
        lower = int((minimum * scale).to_integral_value(rounding="ROUND_CEILING"))
        upper = int((maximum * scale).to_integral_value(rounding="ROUND_FLOOR"))
        scaled = rng.randint(lower, upper)
        if digits == 0:
            value = Decimal(scaled)
        else:
            integer, fraction = divmod(scaled, scale)
            value = Decimal(f"{integer}.{fraction:0{digits}d}")
    return _maybe_negative(
        rng, value, float(profile.get("currency_negative_probability", 0.0))
    )


def _call_support(function, args: tuple, options: dict) -> bool:
    try:
        return bool(function(*args, **options))
    except TypeError:
        return False


def _canonical_options(
    rng: random.Random, locale: str, kind: str, config: RandomConfig
) -> tuple[dict[str, str | int | bool], str | None]:
    language = locale.split("-", 1)[0]
    if language == "es" and kind in {"ordinal", "ordinal_num"}:
        gender = rng.choice(("masculine", "feminine"))
        return {"gender": gender}, f"es-{kind}-{gender}"
    if language == "ru" and kind in {"cardinal", "ordinal"}:
        matrix = (
            {
                "gender": "masculine",
                "case": "nominative",
                "plural": False,
                "animate": False,
            },
            {
                "gender": "feminine",
                "case": "nominative",
                "plural": False,
                "animate": False,
            },
            {
                "gender": "masculine",
                "case": "genitive",
                "plural": False,
                "animate": False,
            },
            {
                "gender": "masculine",
                "case": "dative",
                "plural": False,
                "animate": False,
            },
            {
                "gender": "masculine",
                "case": "accusative",
                "plural": False,
                "animate": True,
            },
            {
                "gender": "masculine",
                "case": "accusative",
                "plural": False,
                "animate": False,
            },
            {
                "gender": "feminine",
                "case": "instrumental",
                "plural": False,
                "animate": False,
            },
            {
                "gender": "masculine",
                "case": "prepositional",
                "plural": False,
                "animate": False,
            },
            {"plural": True, "case": "nominative", "animate": False},
        )
        selected = rng.choice(matrix)
        return selected, f"ru-{kind}-" + "-".join(
            str(value) for value in selected.values()
        )
    return {}, None


def _compat_options(
    rng: random.Random, kind: str, config: RandomConfig
) -> tuple[dict, str | None, str | None, str]:
    variants = [
        variant
        for variant in config.compat_variants
        if variant.get("kind") in {None, kind}
    ]
    options = {}
    variant_id = None
    if variants:
        variant = rng.choice(variants)
        options = {
            key: value
            for key, value in variant.items()
            if key not in {"id", "kind", "transport", "call_variant"}
        }
        variant_id = variant.get("id")
    call_variants = tuple(
        call_variant
        for call_variant in config.compat_call_variants
        if call_variant != "ordinal-bool" or kind == "ordinal"
    ) or ("to",)
    call_variant = rng.choice(call_variants)
    transport = rng.choice(config.compat_transports)
    return (
        options,
        variant_id,
        (None if call_variant == "to" else call_variant),
        transport,
    )


def _is_ordinal_kind(kind: str) -> bool:
    return kind in {"ordinal", "ordinal_num"}


def _candidate(
    rng: random.Random,
    locale: str,
    kind: str,
    profile: dict,
    currency_choices: tuple[str, ...],
    *,
    config: RandomConfig,
    target: str,
) -> tuple[int | Decimal, str | None, dict, str | None, str | None, str]:
    edge_probability = float(profile.get("edge_probability", 0.0))
    if kind in {"cardinal", "ordinal", "ordinal_num", "year"}:
        if kind == "cardinal":
            minimum, maximum, edges = (
                int(profile["cardinal_min"]),
                int(profile["cardinal_max"]),
                _edge_values(),
            )
            value = random_integer(
                rng,
                minimum=minimum,
                maximum=maximum,
                edge_values=edges,
                edge_probability=edge_probability,
            )
            if minimum >= 0:
                value = _maybe_negative(
                    rng, value, float(profile.get("negative_probability", 0.0))
                )
        elif kind in {"ordinal", "ordinal_num"}:
            minimum, maximum, edges = (
                int(profile["ordinal_min"]),
                int(profile["ordinal_max"]),
                _ordinal_edge_values(),
            )
            value = random_integer(
                rng,
                minimum=minimum,
                maximum=maximum,
                edge_values=edges,
                edge_probability=edge_probability,
            )
        else:
            minimum, maximum, edges = (
                int(profile["year_min"]),
                int(profile["year_max"]),
                _year_edge_values(),
            )
            value = random_integer(
                rng,
                minimum=minimum,
                maximum=maximum,
                edge_values=edges,
                edge_probability=edge_probability,
            )
        options, variant_id = (
            _canonical_options(rng, locale, kind, config)
            if target == "canonical"
            else ({}, None)
        )
        if target == "compat":
            options, variant_id, call_variant, transport = _compat_options(
                rng, kind, config
            )
        else:
            call_variant, transport = None, "native"
        return value, None, options, variant_id, call_variant, transport
    if kind == "decimal":
        value = _decimal(rng, profile)
        if target == "compat":
            options, variant_id, call_variant, transport = _compat_options(
                rng, kind, config
            )
        else:
            options, variant_id, call_variant, transport = {}, None, None, "native"
        return value, None, options, variant_id, call_variant, transport
    if kind == "currency":
        currency = rng.choice(currency_choices)
        value = _currency_decimal(rng, profile, currency)
        if target == "compat":
            options, variant_id, call_variant, transport = _compat_options(
                rng, kind, config
            )
        else:
            variants = config.currency_variants_for(locale) or ({"id": "default"},)
            variant = rng.choice(variants)
            options = {key: value for key, value in variant.items() if key != "id"}
            variant_id, call_variant, transport = variant.get("id"), None, "native"
        return value, currency, options, variant_id, call_variant, transport
    raise ValueError(f"unknown case kind: {kind!r}")


def supported_currency_candidates(
    *,
    locale: str,
    oracle_locale: str,
    configured: tuple[str, ...],
    currency_supports: Callable[..., bool],
    oracle_supports: Callable[..., bool],
) -> tuple[str, ...]:
    probe = Decimal("1.01")
    return tuple(
        code
        for code in configured
        if _call_support(currency_supports, (locale, probe, code), {})
        and _call_support(oracle_supports, (oracle_locale, "currency", probe, code), {})
    )


def _default_supports(locale: str, kind: str, value: int | Decimal, **options) -> bool:
    if kind == "decimal":
        from numeralform import DecimalNumber

        return numeralform.supports(
            locale, form="decimal", value=DecimalNumber.from_decimal(value)
        )
    morphology = {
        key: options[key]
        for key in ("gender", "case", "grammatical_number", "animacy")
        if key in options
    }
    if "plural" in options:
        morphology["grammatical_number"] = "plural" if options["plural"] else "singular"
    if "animate" in options:
        morphology["animacy"] = "animate" if options["animate"] else "inanimate"
    syntax = (
        "attributive"
        if locale.split("-", 1)[0] == "es" and kind == "ordinal" and "gender" in options
        else "standalone"
    )
    return numeralform.supports(
        locale, form=kind, value=value, syntax=syntax, morphology=morphology
    )


def _default_currency_supports(
    locale: str, value: Decimal, currency: str, **options
) -> bool:
    if not supports_currency(locale, currency):
        return False
    try:
        render_currency(value, locale=locale, currency=currency, **options)
    except Exception:  # noqa: BLE001
        return False
    return True


def generate_cases(
    *,
    seed: int,
    count: int,
    profile: str = "shared",
    oracle_root: Path | None = None,
    locales: Iterable[str] | None = None,
    kinds: Iterable[str] | None = None,
    currencies: Iterable[str] | None = None,
    config_path: Path = CONFIG_PATH,
    canonical_locales: Iterable[str] | None = None,
    external_locales: Iterable[str] | None = None,
    supports: Callable[..., bool] | None = None,
    currency_supports: Callable[..., bool] | None = None,
    oracle_supports: Callable[..., bool] | None = None,
    oracle_supports_case: Callable[[RandomCase], bool] | None = None,
    variant: str | None = None,
    transport: str | None = None,
    target: str = "canonical",
) -> tuple[tuple[RandomCase, ...], dict[str, int], RandomConfig]:
    if count < 0:
        raise ValueError("case count must be non-negative")
    if target not in {"canonical", "compat"}:
        raise ValueError(f"unknown benchmark target: {target!r}")
    config = load_config(config_path, profile)
    pairs = (
        compatibility_locale_pairs(oracle_root, external_locales=external_locales)
        if target == "compat"
        else shared_locale_pairs(
            oracle_root,
            canonical_locales=canonical_locales,
            external_locales=external_locales,
        )
    )
    pair_by_canonical = {pair.canonical: pair for pair in pairs}
    available_locales = tuple(sorted(pair_by_canonical))
    requested_locales = {
        normalize_locale(locale) for locale in locales or available_locales
    }
    selected_locales = tuple(
        sorted(
            requested
            if target == "compat" or requested in pair_by_canonical
            else _NUM2WORDS_CANONICAL_LOCALE_MAP.get(requested, requested)
            for requested in requested_locales
        )
    )
    if not set(selected_locales) <= set(available_locales):
        raise ValueError(
            "requested locales are not shared: "
            + ", ".join(sorted(set(selected_locales) - set(available_locales)))
        )
    selected_kinds = tuple(kinds or CASE_KINDS)
    if not selected_kinds or not set(selected_kinds) <= set(CASE_KINDS):
        raise ValueError(
            "requested kinds must be selected from the supported case kinds"
        )
    profile_values = config.values
    selected_currencies = tuple(currencies or profile_values["currencies"])
    if not selected_currencies:
        raise ValueError("at least one currency is required")
    unknown_currencies = set(selected_currencies) - set(
        profile_values["currency_minor_units"]
    )
    if unknown_currencies:
        raise ValueError(
            "currency minor units are not configured: "
            + ", ".join(sorted(unknown_currencies))
        )
    rng = random.Random(seed)
    supports = supports or _default_supports
    currency_supports = currency_supports or _default_currency_supports
    oracle_supports = oracle_supports or (lambda *args: True)
    generated: list[RandomCase] = []
    seen: set[tuple] = set()
    rejected = {
        "generation_rejected_numeralform_unsupported": 0,
        "generation_rejected_oracle_unsupported": 0,
        "generation_rejected_duplicate": 0,
        "generation_rejected_semantic_incompatibility": 0,
    }
    max_attempts = max(
        count * int(profile_values.get("max_attempt_multiplier", 30)), count + 1
    )
    attempts = 0
    while len(generated) < count and attempts < max_attempts:
        attempts += 1
        floor_size = (
            len(selected_locales) * len(selected_kinds) if target == "canonical" else 0
        )
        if attempts <= floor_size:
            floor_index = attempts - 1
            locale = selected_locales[floor_index // len(selected_kinds)]
            kind = selected_kinds[floor_index % len(selected_kinds)]
        else:
            locale = rng.choice(selected_locales)
            kind = weighted_choice(
                rng, {key: config.weights[key] for key in selected_kinds}
            )
        oracle_locale = pair_by_canonical[locale].oracle
        if profile == "shared" and any(
            exclusion.get("locale") == locale and exclusion.get("kind") == kind
            for exclusion in config.shared_exclusions
        ):
            rejected["generation_rejected_semantic_incompatibility"] += 1
            continue
        value, currency, options, variant_id, call_variant, case_transport = _candidate(
            rng,
            locale,
            kind,
            profile_values,
            selected_currencies,
            config=config,
            target=target,
        )
        if (
            profile == "shared"
            and _is_ordinal_kind(kind)
            and value == 0
            and locale.split("-", 1)[0] in config.shared_ordinal_zero_excluded_languages
        ):
            rejected["generation_rejected_semantic_incompatibility"] += 1
            continue
        if (
            profile == "shared"
            and locale.split("-", 1)[0] == "ru"
            and kind in {"cardinal", "ordinal"}
            and options
            and abs(value) > 999
        ):
            rejected["generation_rejected_semantic_incompatibility"] += 1
            continue
        if variant is not None and variant_id != variant:
            continue
        if transport is not None and case_transport != transport:
            continue
        if target == "canonical" and profile in {"common", "numeralform", "shared"}:
            supported = (
                _call_support(currency_supports, (locale, value, currency), options)
                if kind == "currency"
                else _call_support(supports, (locale, kind, value), options)
            )
            if not supported:
                rejected["generation_rejected_numeralform_unsupported"] += 1
                continue
        serialized = SerializedRandomValue.from_python(value)
        if profile == "shared":
            if oracle_supports_case is not None:
                probe_case = RandomCase(
                    schema_version=SCHEMA_VERSION,
                    generator_version=GENERATOR_VERSION,
                    seed=seed,
                    index=len(generated),
                    case_id="probe",
                    locale=locale,
                    kind=kind,
                    surface="",
                    value=serialized,
                    currency=currency,
                    oracle_locale=oracle_locale,
                    options=options,
                    variant_id=variant_id,
                    call_variant=call_variant,
                    transport=case_transport,
                )
                supported = oracle_supports_case(probe_case)
            else:
                supported = _call_support(
                    oracle_supports, (oracle_locale, kind, value, currency), options
                )
            if not supported:
                rejected["generation_rejected_oracle_unsupported"] += 1
                continue
        identity = (
            locale,
            kind,
            serialized.value,
            currency,
            json.dumps(options, sort_keys=True),
            variant_id,
            call_variant,
            case_transport,
        )
        if profile in {"common", "numeralform", "shared"} and identity in seen:
            rejected["generation_rejected_duplicate"] += 1
            continue
        seen.add(identity)
        surface, tags = surface_for(locale, kind, value, currency=currency, rng=rng)
        generated.append(
            RandomCase(
                schema_version=SCHEMA_VERSION,
                generator_version=GENERATOR_VERSION,
                seed=seed,
                index=len(generated),
                case_id=f"random-v{GENERATOR_VERSION}:{seed}:{len(generated):06d}",
                locale=locale,
                kind=kind,
                surface=surface,
                value=serialized,
                currency=currency,
                tags=tags,
                oracle_locale=oracle_locale,
                options=options,
                variant_id=variant_id,
                call_variant=call_variant,
                transport=case_transport,
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
    "SCHEMA_VERSION",
    "_NUM2WORDS_CANONICAL_LOCALE_MAP",
    "RandomConfig",
    "SharedLocale",
    "_currency_edge_values",
    "_decimal_edge_values",
    "_default_currency_supports",
    "_default_supports",
    "_is_ordinal_kind",
    "_ordinal_edge_values",
    "_year_edge_values",
    "compatibility_locale_pairs",
    "generate_cases",
    "load_config",
    "normalize_locale",
    "random_integer",
    "shared_locale_pairs",
    "shared_locales",
    "supported_currency_candidates",
    "weighted_choice",
]
