# Numeralform

Numeralform is a typed, locale-aware number-to-words engine for Python. It preserves semantic values, supports explicit syntax and reviewed morphology, exposes capability discovery, and provides a deterministic `num2words` compatibility adapter.

## Install

```bash
python -m pip install numeralform
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
# result.locale == "en", result.requested_locale == "en-US"
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

## Supported locales

`locales()` returns only locales with reviewed canonical renderers. `known_locales()` includes registered compatibility placeholders. Placeholder locales have empty canonical capabilities and reject rendering instead of returning raw numeric notation.

```python
from numeralform import capabilities, locales, supports

print(locales())
print(capabilities("ru"))
supports("ru", form="cardinal", syntax="attributive", value=21)
```

## Compatibility

```python
from numeralform.compat import num2words

num2words(42, lang="en")
```

The runtime adapter is deterministic and does not import upstream `num2words`. The compatibility profile is pinned to Git revision `07814cb114157f582c40a00119c2e9faba8dcee2` with package metadata `0.5.14`; the oracle is used only by generation tooling.

## Errors

Invalid values and requests raise `NumeralFormError` subclasses. Unsupported locales, forms, morphology, styles, and feature combinations are rejected explicitly.

## CLI

```bash
numeralform 42 --locale en
numeralform 0042 --locale en --digits
numeralform --version
numeralform --list-locales
numeralform --capabilities ru
```

## Development

See [the API reference](docs/api.md), [locale inventory](docs/locales/README.md), and [release procedure](docs/releasing.md). Run the test suite with:

```bash
python -m unittest discover -s tests -v
```
