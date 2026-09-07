# Spanish (`es`)

## Contract

- Canonical locale: `es`
- Forms: cardinal, ordinal, digits, decimal, fraction, year
- Syntax: cardinal standalone or attributive; ordinal standalone, ordinal-adjectival, or attributive; other forms are standalone.
- Morphology: masculine/feminine cardinal and ordinal morphology is accepted only in attributive contexts where the profile advertises it. Case, animacy, grammatical number, and noun class are unsupported.
- Styles: `default` only.
- Cardinal range: `-999,999,999..999,999,999`.
- Ordinal range: `0..20`.
- Fraction denominator range: `2..20`.
- Year: explicit form using ordinary Spanish cardinal realization.

## Canonical examples

```text
21 standalone                         -> veintiuno
21 attributive masculine              -> veintiún
21 attributive feminine               -> veintiuna
31 attributive masculine              -> treinta y un
121 attributive masculine             -> ciento veintiún
221 attributive feminine              -> doscientas veintiuna
21,000 attributive masculine          -> veintiún mil
1.20                                  -> uno punto dos cero
1/2                                   -> un medio
```

Digit sequences preserve leading zeroes. Masculine apocopation is component-aware: it transforms the final component (`uno`, `veintiuno`, or `... y uno`) rather than replacing arbitrary text.

## Limitations and decisions

- Feminine hundreds are reviewed for attributive output (`doscientas`, `trescientas`, and so on).
- Ordinals intentionally stop at 20 until larger composition is independently reviewed; requests such as ordinal 30 raise `InvalidValueError`.
- Fraction denominators outside the reviewed range are rejected.
- Year does not arise from magnitude inference; callers must request `form="year"`.

## References

- Real Academia Española, _Diccionario panhispánico de dudas_, “numerales”: https://www.rae.es/dpd/numerales
- Real Academia Española, _Ortografía de la lengua española_ overview: https://www.rae.es/obras-academicas/ortografia
- Project-rendered regression matrix in `tests/test_numeralform.py` and `tests/test_hardening.py`.
