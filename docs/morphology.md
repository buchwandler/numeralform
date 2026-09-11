# Canonical morphology review boundaries

Numeralform keeps common morphology dimensions typed while allowing locale-specific
case identifiers. Case strings use lowercase English/UD-style names where a
shared inventory exists (`nominative`, `genitive`, `accusative`, `partitive`,
`inessive`, and so on); locale-specific extensions remain open strings and are
not coerced into the universal `Case` enum.

## Reviewed domains

- Russian cardinal/ordinal forms cover gender, case, animacy, grammatical number,
  and scale interactions in the reviewed regression matrix.
- Spanish attributive cardinal forms cover masculine apocopation and compound
  values in the reviewed regression matrix.
- Finnish cardinal, ordinal, and numeric-ordinal forms are reviewed for nominative
  singular values from 0 through 999,999,999,999. The broader fifteen-case
  implementation remains an experiment outside the reviewed nominative singular
  surface. Requests outside this domain are rejected rather than advertised.
- Currency phrases are validated as a sibling subsystem: numeral realization
  and currency-noun agreement are separate contracts.

Capabilities describe this reviewed truth, not the intended future inventory.
New case or agreement support must add native-reviewed unit, teen, tens,
compound, hundred, thousand, and scale-boundary fixtures before widening a
profile.
