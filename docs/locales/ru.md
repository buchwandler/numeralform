# Russian (`ru`)

## Contract

- Canonical locale: `ru`
- Forms: cardinal, ordinal, digits, decimal, fraction, year
- Syntax: cardinal standalone/attributive; ordinal standalone/ordinal-adjectival; other forms are standalone.
- Morphology: cardinal gender supports masculine, feminine, and neuter. Case, animacy, grammatical number, and noun class are deliberately unsupported.
- Styles: `default` only.
- Cardinal and decimal integer range: magnitude below `1,000,000,000`.
- Ordinal range: `0..29`.
- Fraction denominator range: `2..10`.
- Year: explicit form using ordinary Russian cardinal realization.

## Canonical examples

```text
1 masculine                 -> один
1 feminine                  -> одна
1 neuter                    -> одно
21,000                      -> двадцать одна тысяча
22,000                      -> двадцать две тысячи
25,000                      -> двадцать пять тысяч
21,000,000                  -> двадцать один миллион
22,000,000                  -> двадцать два миллиона
25,000,000                  -> двадцать пять миллионов
1/2                         -> одна вторая
2/3                         -> два третьих
3/4                         -> три четвёртых
5/8                         -> пять восьмых
```

Scale nouns use the final two digits for the one/few/many category, including the 11–14 exception. Thousands use feminine group agreement; millions use masculine group agreement.

## Limitations and decisions

- Values at or above one billion are rejected until larger-scale vocabulary is reviewed; no improvised `тысяча миллионов` output is allowed.
- Ordinals stop at 29 to avoid speculative composition and accidental recursion.
- Fractions use a reviewed common-denominator set; unreviewed denominator morphology is rejected.
- Case and animacy are future capability dimensions, not accepted-but-ignored options.
- Year is explicit and is not inferred from a four-digit cardinal.

## References

- Gramota.ru, Russian language reference and consultation portal: https://gramota.ru/
- Russian Academy of Sciences, _Russian Grammar_ reference entry point: https://rusgram.ru/
- Project-rendered regression matrix in `tests/test_numeralform.py` and `tests/test_hardening.py`.
