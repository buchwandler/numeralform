# Romanian

## Locale IDs

- Canonical base locale: `ro`

## Supported forms

- `cardinal`
- `digits` with leading zeros preserved
- `decimal` with visible fractional precision
- `year`
- `ordinal_num` through the canonical numeric-ordinal strategy

## Numeric domain

Cardinal and decimal integer parts support `-999999999` through `999999999`. Years support non-negative values through `9999`.

## Default standalone policy

The renderer uses the documented standalone lexical convention for Romanian and does not infer context from surrounding text.

## Morphology

Only unmarked standalone morphology is advertised. Explicit unsupported gender, case, state, or agreement requests raise `UnsupportedMorphologyError`.

## Decimal policy

The integer part is rendered canonically, followed by the locale decimal marker and each fractional digit as a spoken digit. Trailing zeroes are semantic.

## Ordinal policy

Numeric ordinals are separate from word ordinals. Word ordinal support is advertised only where a reviewed lexical surface is available.

## Year policy

Years have an explicit form and do not activate hidden cardinal or compatibility heuristics.

## Currency support

Currency support is independent of numeral coverage. English fallback does not imply localized currency support.

## Regional behavior

- Related regional registrations: None
- Script and orthography are fixed by the canonical locale policy.

## Validation sources

- Pinned `num2words` behavioral oracle at commit `07814cb114157f582c40a00119c2e9faba8dcee2`.
- CLDR/ICU where a strict rule set is available.
- Independent language and orthography references.

## Known limitations

Contextual agreement, complete denominator morphology, and unreviewed localized currency lexicons remain outside the initial standalone contract.
