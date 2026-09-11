# Locale capability inventory

The canonical inventory is generated from runtime capabilities. `locales()` lists only independently reviewed renderers. `known_locales()` also includes compatibility registrations that intentionally expose no canonical forms.

## Reviewed canonical locales

The current executable renderers cover:

- Czech: `cs`
- English and regional English: `en`, `en-US`, `en-GB`, `en-IN`, `en-NG`
- Finnish: `fi`
- French and regional French: `fr`, `fr-BE`, `fr-CH`, `fr-DZ`
- German: `de`
- Italian: `it`
- Japanese: `ja`
- Korean: `ko`
- Portuguese: `pt`, `pt-BR`, `pt-PT`
- Russian: `ru`
- Spanish regional variants: `es`, `es-CO`, `es-CR`, `es-GT`, `es-NI`, `es-VE`
- Swedish: `sv`
- Thai: `th`
- Vietnamese: `vi`

Capability profiles define the supported forms, syntaxes, morphology, styles, and numeric domains. They are the source of truth for `supports()` and the CLI capability report.

## Compatibility-only registrations

Other upstream locale identifiers remain discoverable through `known_locales()` for compatibility reporting. They have empty canonical capabilities and raise an explicit unsupported error when passed to `render()`.

See the generated [runtime capability matrix](capability-matrix.md) for every canonical locale's forms and advertised integer maxima. Use `capabilities(locale)` for exact syntax, morphology, style, and locale-feature constraints; the matrix is checked against runtime data in the test suite.

Finnish cardinal, ordinal, and numeric-ordinal profiles share the reviewed nominative-singular integer domain `0..999,999,999,999`.
