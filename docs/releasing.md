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
python -m build --no-isolation
```

The default suite does not acquire or read benchmark data and does not require network access, ICU, or an external `num2words` installation.

## Compatibility and reference benchmark gate

When compatibility claims require reference evidence, run the separate benchmark workflow or execute:

```bash
python -m benchmarks.download num2words
python -m benchmarks.run all
python -m pytest benchmarks/tests
```

The num2words checkout is pinned and verified. CLDR requires the documented pinned ICU/PyICU maintainer environment. Benchmark corpora, oracle checkouts, and reports remain local under ignored `benchmarks/data/`.

## Artifacts

Inspect wheel and sdist metadata. Their package metadata and filenames must report `0.1.0`. Install the wheel and sdist in clean environments and verify:

```python
import numeralform

assert numeralform.__version__ == "0.1.0"
assert numeralform.render(42, locale="en") == "forty-two"
```

Also run `numeralform --version`, the rendering command, and verify `numeralform/py.typed` is present in the wheel.

Create the `v0.1.0` tag only after required core and benchmark gates pass. Publish using the project publishing policy, then repeat the version and rendering smoke tests from the published artifacts.
