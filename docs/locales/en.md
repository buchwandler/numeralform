# English (`en`, `en-US`, `en-GB`)

## Contract

- Canonical locales: `en`, `en-US`, and `en-GB`
- Forms: cardinal, ordinal, digits, decimal, fraction, year
- Syntax: cardinal supports standalone/attributive/ordinal-adjectival contexts; ordinal supports standalone and ordinal-adjectival; other forms are standalone.
- Morphology: no gender, case, animacy, number, or noun-class morphology.
- Styles: `default` for all forms; `british-and` for cardinals only.
- Cardinal and ordinal range: `-999,999,999,999..999,999,999,999` for cardinal; non-negative values in the same magnitude for ordinal.
- Year range: `0..9999`.

`en` is generic project English and uses the U.S.-style omission of British cardinal `and`. `en-US` is the explicit U.S. English locale with the same default. `en-GB` is explicit British English and uses `and` in the reviewed cardinal positions by default.

None of these canonical locales insert commas between spelled-out scale groups. The currency connector remains `and` in both regional locales, while cardinal-internal grammar follows the locale.

## Canonical examples

```text
42       -> forty-two
105 en-US -> one hundred five
105 en-GB -> one hundred and five

98100.3 en-US -> ninety-eight thousand one hundred point three
98100.3 en-GB -> ninety-eight thousand one hundred point three

582378.922 en-US
  -> five hundred eighty-two thousand three hundred seventy-eight point nine two two
582378.922 en-GB
  -> five hundred and eighty-two thousand three hundred and seventy-eight point nine two two

USD 531.84 en-US
  -> five hundred thirty-one dollars and eighty-four cents
USD 531.84 en-GB
  -> five hundred and thirty-one dollars and eighty-four cents

GBP 928.11 en-US
  -> nine hundred twenty-eight pounds and eleven pence
GBP 928.11 en-GB
  -> nine hundred and twenty-eight pounds and eleven pence

40062400 -> forty million sixty-two thousand four hundred
```

Digit sequences preserve every source digit, and `DecimalNumber("1", "20")` renders as `one point two zero`.

## Limitations and decisions

- The renderer rejects magnitudes requiring an unreviewed scale instead of inventing phrases such as `one thousand billion`.
- `british-and` remains an explicit cardinal style and is supported on `en` and `en-US`; it is the default behavior of `en-GB`.
- An implicit regional default is reported as `style="default"`, not as `british-and`.
- Year interpretation is explicit: Numeralform never infers a year from an integer.

## References

- Oxford Learner's Dictionaries, number: https://www.oxfordlearnersdictionaries.com/definition/english/number_1
- Project-rendered regression matrix in `tests/test_english_regional.py`.
