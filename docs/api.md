# API reference

Numeralform exposes a strict canonical API. Inputs are semantic values and
requests; locale capabilities decide which forms and grammatical features can be
executed.

## Rendering facade

```python
from numeralform import render, realize, render_request

render(42, locale="en")  # "forty-two"
realize(42, locale="en-US").locale  # "en-US"
render_request(NumeralRequest(42, "en"))  # "forty-two"
```

`render(value, *, locale, ...)` returns text. `realize` accepts the same value
arguments or a `NumeralRequest` and returns `NumeralResult`. `render_request` is
the structured-request spelling. If `form` is omitted it is inferred from the
semantic input type; an incompatible explicit form raises `InvalidValueError`.

## Semantic values

- `NumericInput` accepts `int`, `Decimal`, `Fraction`, `DigitSequence`,
  `DecimalNumber`, and `FractionNumber`.
- `NumericValue` is the typed runtime union excluding `Decimal` and `Fraction`.
- `DigitSequence("0042")` preserves leading zeroes.
- `DecimalNumber("1", "20")` preserves visible fractional precision.
- `FractionNumber(2, 3)` stores a numerator and positive denominator.

## Requests and results

`NumeralRequest` contains a numeric value, locale, optional `NumeralForm`,
`Syntax`, `Morphology`, style, and `LocaleFeatures`. Its constructor accepts the
same enum/string coercions as the public convenience facade. `NumeralResult`
contains rendered text, resolved/requested locale, effective form/style, syntax,
morphology, and features.

## Grammar

`Gender`, `Case`, `Animacy`, and `Syntax` are string enums. `Morphology` provides
`gender`, `case`, `animacy`, `grammatical_number`, `noun_class`, `definiteness`,
and `state`. `LocaleFeatures` is an immutable mapping for locale-specific
features; non-mapping containers and unsupported values raise
`InvalidRequestError`.

## Capabilities

- `locales()` returns reviewed executable canonical locales.
- `known_locales()` includes compatibility registrations as well.
- `capabilities(locale)` returns `LocaleCapabilities` and exact
  `CapabilityProfile` records.
- `supports(locale, form=..., syntax=..., morphology=..., style=..., value=...)`
  checks whether the complete request can execute.
- `NumericDomain` describes integer bounds and decimal/fraction support.
- `FeatureSpec` describes an allowed feature and its values.
- `CapabilityProfile` describes one form's syntax, morphology, styles, features,
  and domain; `LocaleCapabilities` aggregates profiles and notes.
- The generated [runtime capability matrix](locales/capability-matrix.md)
  summarizes forms and integer maxima without replacing exact profile data.

## Locale utilities

`canonicalize_locale("EN_us")` returns `"en-US"`; `parse_locale` returns a
`Locale` structure; `fallback_chain` returns the ordered locale fallback tags;
`resolve_locale` returns an executable canonical locale. The parser supports the
`is_registered` reports whether an exact canonical locale tag is registered; it does not imply that the locale has reviewed executable forms.
common BCP-47-style language/script/region/variant subset. Extensions and
private-use subtags such as `en-u-nu-latn` and `x-private` are not supported in
v0.1.0.

## Currency

`MoneyAmount`, `CurrencyRequest`, and `CurrencyResult` model structured currency
operations. `render_currency` returns text and `realize_currency` returns a
`CurrencyResult`; see the dedicated [currency guide](currency.md).
`supports_currency` checks terminology after canonical locale resolution.

```python
from numeralform import MoneyAmount, render_currency

render_currency(MoneyAmount(1, 50, "USD"))  # "one dollar and fifty cents"
```

## Errors

All canonical failures derive from `NumeralFormError`: `InvalidValueError`,
`InvalidRequestError`, `UnsupportedLocaleError`, `UnsupportedFormError`,
`UnsupportedMorphologyError`, `UnsupportedStyleError`, and
`UnsupportedCurrencyError`. The compatibility namespace translates these into
legacy exception types where required.

## Renderer registration policy

Renderer registration and resolution are provisional implementation details in
v0.1.0 and are intentionally not exported from the top-level package. Use the
stable discovery functions (`locales`, `known_locales`, `capabilities`,
`supports`, and `resolve_locale`) instead. A future release may publish a
complete, documented extension protocol.

## Compatibility namespace

Use `numeralform.compat.num2words` for the tested pinned `num2words` 0.5.14
surface. It is separate from the strict canonical API, retains legacy coercion
and option translation, and does not require upstream `num2words` at runtime.

## Year semantics

`form="year"` is a spoken year expression, not an alias for cardinal rendering.
English uses locale-specific grouping, Korean appends `년`, and German and
Japanese use their canonical year realization. Japanese era conversion is
available only through compatibility.
