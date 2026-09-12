[![PyPI - Version](https://img.shields.io/pypi/v/numeralfrom)](https://pypi.org/project/numeralform/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/numeralform)
![PyPI - Downloads](https://img.shields.io/pypi/dm/numeralform)
[![codecov](https://codecov.io/gh/buchwandler/numeralform/graph/badge.svg?token=gdXfPp7RTe)](https://codecov.io/gh/buchwandler/numeralform)

# Numeralform

Numeralform is a typed, locale-aware number-to-words engine for Python. It provides canonical executable support for all 49 Spokenform base language families plus reviewed regional variants. It preserves semantic values, supports explicit syntax and reviewed morphology, exposes capability discovery, and provides a deterministic `num2words` compatibility adapter.

## Install

```bash
python -m pip install numeralform
```

For development:

```bash
python -m pip install -e ".[test]"
```

## Quick start

```python
from numeralform import DecimalNumber, DigitSequence, render, realize

render(42, locale="en")
# "forty-two"
render(DigitSequence("0042"), locale="en")
# "zero zero four two"
render(DecimalNumber("1", "20"), locale="en")
# "one point two zero"
result = realize(42, locale="en-US")
# result.locale == "en-US", result.requested_locale == "en-US"
```

## Why Numeralform

| Capability           | Numeralform                     | Legacy `num2words` style |
| -------------------- | ------------------------------- | ------------------------ |
| Leading zeros        | Preserved by `DigitSequence`    | Usually lost             |
| Decimal precision    | Preserved by `DecimalNumber`    | Coerced permissively     |
| Grammar              | Typed `Morphology` and `Syntax` | Locale kwargs            |
| Capabilities         | Exact reviewed profiles         | Limited discovery        |
| Unsupported requests | Explicit errors                 | Varies                   |
| Compatibility        | Separate deterministic adapter  | Single permissive API    |

## Compatibility

```python
from numeralform.compat import num2words

num2words(42, lang="en")
```

The runtime adapter is deterministic and does not import upstream `num2words`. The compatibility profile is pinned to Git revision `07814cb114157f582c40a00119c2e9faba8dcee2` with package metadata `0.5.14`.

## Development tests

The default suite contains only small Numeralform tests. It needs no benchmark data, network access, ICU, or external `num2words` package:

```bash
python -m pytest
```

Coverage, lint, formatting, and build checks are described in [the release procedure](docs/releasing.md).

## Explicit benchmarks

Oracle, corpus, differential, and upstream compatibility work is separate from unit tests:

```bash
python -m benchmarks.download num2words
python -m benchmarks.run num2words
python -m benchmarks.run cldr
python -m benchmarks.run all
python -m pytest benchmarks/tests
```

Benchmark data and reports are generated locally under `benchmarks/data/` and are not required for normal tests.

## CLI

```bash
numeralform 42 --locale en
numeralform 0042 --locale en --digits
numeralform --version
numeralform --list-locales
numeralform --capabilities ru
```

See [the API reference](docs/api.md), [locale inventory](docs/locales/README.md), [compatibility contract](docs/compatibility.md), and [release procedure](docs/releasing.md).
