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

The corpus checker verifies JSONL ordering, NFC output, manifest hashes, case counts, exception records, and mismatch dimensions. A benchmark command returns non-zero when comparison mismatches or when required oracle/version checks fail. Reports group differences by locale, form, value range, expectation kind, and difference shape.

The default test extra includes pytest and coverage only. ICU/PyICU and the upstream num2words oracle are benchmark-only prerequisites. The package build includes `numeralform` and does not package this directory.
