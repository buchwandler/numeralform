# English (`en`)

## Contract

- Canonical locale: `en`
- Forms: cardinal, ordinal, digits, decimal, fraction, year
- Syntax: cardinal supports standalone/attributive/ordinal-adjectival contexts; ordinal supports standalone and ordinal-adjectival; other forms are standalone.
- Morphology: no gender, case, animacy, number, or noun-class morphology.
- Styles: `default` for all forms; `british-and` for cardinals only.
- Cardinal and ordinal range: `-999,999,999,999..999,999,999,999` for cardinal; non-negative values in the same magnitude for ordinal.
- Year range: `0..9999`.

## Canonical examples

```text
42       -> forty-two
105      -> one hundred five
105 + british-and -> one hundred and five
1001 + british-and -> one thousand and one
1900 (year) -> nineteen hundred
1905 (year) -> nineteen oh five
1999 (year) -> nineteen ninety-nine
2000 (year) -> two thousand
2024 (year) -> twenty twenty-four
1/2      -> one half
```

Digit sequences preserve every source digit, and `DecimalNumber("1", "20")` renders as `one point two zero`.

## Limitations and decisions

- The renderer rejects magnitudes requiring an unreviewed scale instead of inventing phrases such as `one thousand billion`.
- `british-and` is a deliberate cardinal style and is not accepted for digitwise, decimal, fraction, ordinal, or year rendering.
- Year interpretation is explicit: Numeralform never infers a year from an integer.

## References

- Oxford Learner's Dictionaries, number: https://www.oxfordlearnersdictionaries.com/definition/english/number_1
- Project-rendered regression matrix in `tests/test_numeralform.py` and `tests/test_hardening.py`.
