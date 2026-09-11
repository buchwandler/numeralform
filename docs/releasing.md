# Releasing Numeralform

## Core gate

Run the hermetic product checks:

```bash
python -m pip install -e ".[test]"
python -m pytest
python -m coverage run -m pytest
python -m coverage report
ruff check .
ruff format --check .
python -m mypy tests/typing_consumer.py --strict --follow-imports=skip
python -m build --sdist --wheel --no-isolation
python scripts/check_artifact.py dist
twine check dist/*
```

The default suite does not acquire or read benchmark data and does not require
network access, ICU, or an external `num2words` installation. The artifact check
requires a wheel Summary, `numeralform/py.typed`, no `benchmarks/` or `.ledger/`
contents, and required license/readme/package sources in the sdist. Verify the
wheel from outside the repository root:

```bash
python -m pip install --force-reinstall --no-deps dist/*.whl
cd /tmp
python -I -c 'import numeralform; assert numeralform.__version__ == "0.1.0"; assert numeralform.render(42, locale="en") == "forty-two"'
```

## Compatibility and reference benchmark gate

When compatibility claims require reference evidence, run the separate benchmark
workflow or execute:

```bash
python -m benchmarks.download num2words
python -m benchmarks.run num2words
python -m benchmarks.randomized --cases 10000 --seed 20260910 --target canonical --fail-on-unaccepted --fail-on-coverage-gap
python -m benchmarks.randomized --cases 10000 --seed 20260910 --target compat --fail-on-diff --fail-on-coverage-gap
python -m pytest benchmarks/tests
```

The num2words checkout is pinned and verified. CLDR requires the documented pinned
ICU/PyICU maintainer environment. Benchmark corpora, oracle checkouts, and reports
remain local under ignored `benchmarks/data/` and must be archived for a release
candidate. Do not add the external oracle to ordinary unit CI.

## Release evidence

Releaseledger is the source of release audit evidence. Refresh its audit against
the actual candidate commit, resolve stale or removed paths, validate the audit,
and regenerate `docs/changelog.md` before tagging. Current benchmark paths are
`benchmarks/validation`, `benchmarks/tests`, and `benchmarks/config`; removed
`tools/validation` paths must not appear in release evidence.

## Artifacts and tag

Inspect wheel and sdist metadata. Their package metadata and filenames must report
`0.1.0`. Create the `v0.1.0` tag only after required core and benchmark gates pass.
Publish using the project publishing policy, then repeat the version and rendering
smoke tests from the published artifacts.
