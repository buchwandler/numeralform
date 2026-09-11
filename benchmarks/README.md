# Numeralform benchmarks

`tests/` contains hermetic unit tests for Numeralform. `benchmarks/` owns checks that compare Numeralform with external references, generated corpora, or upstream projects. Benchmark tests run only when explicitly requested:

```bash
python -m pytest benchmarks/tests
```

## Pinned num2words benchmark

Acquire the exact oracle checkout:

```bash
python -m benchmarks.download num2words
```

The downloader verifies repository `savoirfairelinux/num2words`, commit `07814cb114157f582c40a00119c2e9faba8dcee2`, and the checkout module path. A wrong existing revision is rejected unless `--replace` is explicitly supplied. Site-packages is never used as a substitute.

Run generation and comparison:

```bash
python -m benchmarks.run num2words
```

## Randomized num2words differential benchmark

This suite generates reproducible semantic numeral requests, compares canonical Numeralform with the pinned external num2words checkout, and records exact matches, audited accepted variants, true mismatches, and renderer errors. Canonical comparisons report exact parity and semantic parity separately. The compatibility target remains exact. The displayed surface string is diagnostic metadata. Typed values, locale, form, and currency are passed explicitly to both implementations, so strings such as `1.23 $` are never parsed by either renderer.
The generator uses a deterministic locale/form floor before edge-biased fuzz filling. Coverage is recorded in `summary.json` with expected and covered locales, forms, option profiles, currencies, transports, call variants, numeric boundaries, missing cells, and per-cell min/median/max counts. Pass `--fail-on-coverage-gap` to make missing required dimensions fail the run.

The canonical target uses the shared canonical/oracle intersection. The compatibility target uses the pinned oracle locales supported by the compatibility adapter and independently composes transport, dispatch, and option-profile dimensions. The report calls generated profiles `option_profile_id`; comparator `variant` remains reserved for accepted canonical alternatives.
The expanded seed-105 audit intentionally surfaces unaccepted morphology differences instead of hiding them. Current findings are Spanish ordinal gender forms and Russian accusative morphology; these remain differential failures requiring either an explicit equivalence rule backed by negative controls or a renderer fix. They are reported in `differences.jsonl` and are not counted as accepted variants.


### Variant policy

`variant` means a semantically accepted alternative spelling, terminology, grammar, or presentation that preserves the requested numeric value and locale semantics. It does not mean exact reproduction of num2words. Every non-surface variant uses a stable named equivalence rule, and comparator rules never normalize signs, numeric tokens, malformed morphology, unsupported options, or locale fallback.

The shared profile probes the exact generated currency options against both implementations. Unsupported option profiles and oracle domains without a meaningful form, including configured ordinal-zero cases, are rejected during generation and reported as generation rejections rather than oracle errors.
Acquire the pinned oracle before running it:

```bash
python -m benchmarks.download num2words
```

Run a reproducible common-profile sample:

```bash
python -m benchmarks.randomized --cases 10000 --seed 20260910
```

Use `--profile stress` for broader domains, repeat `--locale`, `--kind`, or `--currency` to filter cases, and use `--record-all` to retain matches. Text differences are diagnostic by default. Add `--fail-on-diff` when a strict experiment should return exit code 1 for any non-exact result, including an accepted variant. Use `--fail-on-unaccepted` to ignore accepted variants but fail true mismatches and execution errors. Infrastructure and configuration failures return exit code 2.
Reports are written under `benchmarks/data/results/num2words-random/`:

```text
summary.json       schema v2 provenance, counts, parity, and breakdowns
differences.jsonl  every non-exact result with replayable semantic data and variant rules
report.txt         grouped human-readable differences, including variant rules
all-results.jsonl  optional complete result stream
```

Replay a recorded case without regenerating it:

```bash
python -m benchmarks.randomized \
  --replay benchmarks/data/results/num2words-random/differences.jsonl \
  --case-id random-v1:20260910:000123
```

The top-level convenience target is explicit and is not included in `python -m benchmarks.run all`:

```bash
python -m benchmarks.run num2words-random
```

## CLDR benchmark

Run this in the pinned ICU/PyICU maintainer environment:

```bash
python -m benchmarks.run cldr
```

Run both independent suites with:

```bash
python -m benchmarks.run all
```

CLDR configuration is in `benchmarks/config/cldr.toml`. num2words configuration is in `benchmarks/config/num2words.toml`. Both generators reject oracle or version drift.

## Data and reports

All acquired and generated state is local and ignored by git:

- corpora: `benchmarks/data/corpora/`
- external oracle checkouts: `benchmarks/data/oracles/`
- reports: `benchmarks/data/results/`

Only `.gitkeep` sentinels are tracked. Remove local benchmark state with:

```bash
rm -rf benchmarks/data/corpora/* benchmarks/data/oracles/* benchmarks/data/results/*
```

The corpus checker verifies JSONL ordering, NFC output, manifest hashes, case counts, exception records, and mismatch dimensions. A benchmark command returns non-zero when comparison mismatches or when required oracle/version checks fail. Reports group differences by locale, form, value range, expectation kind, difference shape, and accepted equivalence rule.
The default test extra includes pytest and coverage only. ICU/PyICU and the upstream num2words oracle are benchmark-only prerequisites. The package build includes `numeralform` and does not package this directory.
