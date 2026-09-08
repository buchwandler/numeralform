# API reference

## Rendering

```python
render(value, *, locale, form=None, syntax="standalone", morphology=None,
       style=None, features=None, gender=None, case=None, animacy=None,
       grammatical_number=None, noun_class=None, definiteness=None, state=None)
```

`render` returns text. `realize` accepts the same value arguments or a `NumeralRequest` and returns `NumeralResult`. When `form` is omitted it is inferred from the semantic input type. An explicit incompatible form raises `InvalidValueError`.

`NumericInput` includes `int`, `Decimal`, `Fraction`, `DigitSequence`, `DecimalNumber`, and `FractionNumber`.

## Semantic values

- `DigitSequence` preserves leading zeroes.
- `DecimalNumber` preserves visible fractional precision.
- `FractionNumber` stores a numerator and positive denominator.

## Requests and results

`NumeralRequest` contains value, canonical requested locale, form, syntax, morphology, style, and locale features. `NumeralResult` contains text, resolved locale, requested locale, effective form, effective style, syntax, morphology, and features.

## Grammar

`Morphology` provides typed gender, case, and animacy fields plus locale-extensible grammatical number, noun class, definiteness, and state. `Syntax` is separate from morphology.

`LocaleFeatures` is an immutable mapping for locale-specific features. Unknown or invalid features are rejected by the locale capability profile.

## Capabilities

- `locales()` returns reviewed executable canonical locales.
- `known_locales()` returns built-in and registered locale identifiers.
- `capabilities(locale)` returns exact profiles.
- `supports(locale, form=..., syntax=..., morphology=..., style=..., value=...)` evaluates every supplied constraint.

## Errors

The error hierarchy starts at `NumeralFormError` and includes `InvalidValueError`, `InvalidRequestError`, `UnsupportedLocaleError`, `UnsupportedFormError`, `UnsupportedMorphologyError`, and `UnsupportedStyleError`.

## Compatibility namespace

Use `numeralform.compat.num2words` for the tested pinned `num2words` 0.5.14 surface. It is separate from the strict canonical API and does not require upstream `num2words` at runtime.

## Currency

`render_currency` returns text. `realize_currency` accepts a value or `CurrencyRequest` and returns `CurrencyResult`. Currency options are explicit and unknown options raise `TypeError`.
