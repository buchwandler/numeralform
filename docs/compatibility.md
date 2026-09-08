# num2words compatibility contract

Numeralform targets `savoirfairelinux/num2words` commit
`07814cb114157f582c40a00119c2e9faba8dcee2` (`0.5.14`) through
`numeralform.compat.num2words`.

Compatibility validation is intentionally separate from canonical Numeralform
validation:

- canonical corpora call `numeralform.render` and may retain linguistically
  reviewed differences from historical output;
- compatibility corpora target `compat:num2words-0.5.14`, call the adapter, and
  compare successful strings and exception categories;
- generated cases preserve Python input type, kwargs, oracle provenance, and
  configuration hash;
- normal installation has no runtime dependency on `num2words`.

`compatibility.toml` is the source of generation scope. The maintainer command
is:

```text
python tools/validation/generate_num2words.py --config compatibility.toml --output tests/validation/compatibility/num2words-0.5.14.jsonl
python tools/validation/generate_num2words.py --config compatibility.toml --check
```

Generated compatibility data is behavioral test data, not copied upstream test
source. The external oracle is LGPL-licensed; see the compatibility corpus
notice for provenance boundaries.

## Compatibility superset boundary

The adapter also accepts fraction strings and `precision=` at the legacy boundary.
Currency metadata supports variable minor-unit scales and richer cents behavior.
Sentence conversion, language detection, aviation phraseology, and digit grouping
remain outside the numeral engine.
