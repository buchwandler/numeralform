# Russian

Russian is a reviewed canonical locale with explicit morphology support.

## Forms

- cardinal
- ordinal
- digits
- decimal
- fraction
- year
- numeric ordinal

Cardinal and ordinal values are reviewed through `10**18 - 1`. Negative values are accepted for cardinals and rejected for ordinal forms.

## Morphology

The capability profiles expose:

- gender: masculine, feminine, neuter
- case: nominative, genitive, dative, accusative, instrumental, prepositional, and locative
- animacy: animate and inanimate
- grammatical number: singular and plural
- standalone and attributive cardinal syntax
- standalone and ordinal-adjectival ordinal syntax

Unsupported combinations raise `UnsupportedMorphologyError`; they are not silently ignored.

```python
from numeralform import render

render(2, locale="ru", case="genitive")
render(21, locale="ru", gender="feminine", syntax="attributive")
```
