# numeralform

Locale-aware numeral morphology and spoken-number rendering for Python.

```python
from numeralform import render

render(42, locale="en")
# "forty-two"

render(21, locale="es", syntax="attributive", gender="masculine")
# "veintiún"
```

`numeralform` renders numeric expressions that the caller has already interpreted. It does not find numbers in arbitrary text. Date, time, currency, unit, identifier, NLP, and TTS concerns belong to a higher-level pipeline such as Spokenform.

## Semantic inputs

Use explicit value types when surface information matters:

```python
from numeralform import DecimalNumber, DigitSequence, render

render(DigitSequence("0042"), locale="en")
# "zero zero four two"

render(DecimalNumber("1", "20"), locale="en")
# "one point two zero"
```

Primitive `int`, `decimal.Decimal`, and `fractions.Fraction` values are accepted as convenience inputs. A `DigitSequence` is not an integer: its leading zeroes are preserved. `DecimalNumber` preserves visible fractional precision.

## Structured API

```python
from numeralform import (
    Gender,
    Morphology,
    NumeralForm,
    NumeralRequest,
    Syntax,
    realize,
)

result = realize(NumeralRequest(
    value=21,
    locale="es",
    form=NumeralForm.CARDINAL,
    syntax=Syntax.ATTRIBUTIVE,
    morphology=Morphology(gender=Gender.FEMININE),
))
print(result.text)  # veintiuna
```

`render` returns the canonical string. `realize` returns a `NumeralResult` with the canonical locale, form, style, and morphology used for the request.

## Locale support

The v0.1 architecture proof includes `en`, `es`, and `ru`:

```python
from numeralform import capabilities, locales

print(locales())
print(capabilities("ru").genders)
```

Locale identifiers use BCP-47-style spelling. `en-US` deterministically falls back to `en`; aliases are handled explicitly by `canonicalize_locale`. Capability declarations expose supported forms, syntax, genders, cases, and styles. Unsupported morphology is rejected rather than silently ignored.

The initial renderers provide deterministic cardinals, digit sequences, precision-preserving digitwise decimals, basic ordinals, fractions, and explicit year requests. Spanish supports standalone and attributive gender forms. Russian supports the reviewed v0.1 gender forms for one and two. Czech, German, Chinese, and broad language coverage are future milestones.

## Command line

```bash
python -m numeralform.cli 42 --locale en
python -m numeralform.cli 21 --locale es --syntax attributive --gender masculine
python -m numeralform.cli 0042 --locale en --digits
python -m numeralform.cli --list-locales
python -m numeralform.cli --capabilities ru
```

The CLI is a thin wrapper over the library and does not interpret sentences.

## Development

The Python package lives directly in `./numeralform`, not in a `src` directory. The package version is declared dynamically in `pyproject.toml` and calculated from git metadata by `numeralform._version`, with `0+unknown` as the source-tree fallback when git is unavailable.

```bash
python -m unittest discover -s tests -v
python -m compileall numeralform tests
python -m build --wheel --no-isolation
```

Canonical output is stable behavior. Changes to wording, hyphenation, spacing, diacritics, or regional forms require corresponding tests and release documentation.
