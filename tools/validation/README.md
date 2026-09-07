# External validation tooling

This directory contains development-only validation infrastructure. It is not imported by `numeralform` runtime code.

## Offline checks

```bash
python -m unittest discover -s tests -v
python tools/validation/check.py --corpus tests/validation
```

The checker consumes committed JSONL and verifies exact NFC output, manifest hashes, request decoding, and renderer behavior. It never calls the network or regenerates fixtures.

## CLDR regeneration

The CLDR corpus is generated only in a pinned maintainer environment containing the reviewed ICU/PyICU binding:

```bash
python tools/validation/generate_cldr.py --config validation.toml --output tests/validation/cldr
python tools/validation/generate_cldr.py --config validation.toml --output tests/validation/cldr --check
python tools/validation/generate_cldr.py --list-rule-sets en
```

The configuration names every RBNF rule set explicitly and pins CLDR 48.2. The adapter rejects missing rule sets, oracle version drift, and silent fallback. `--allow-oracle-version` is an explicit review escape hatch and must not be used to silently accept regenerated data.

When upgrading CLDR, regenerate into a temporary directory, inspect a mismatch report and corpus diff, classify upstream/variant/semantic changes, and update canonical output or reviewed exceptions explicitly. Never track CLDR `main` or overwrite expected output automatically.

`generate_num2words.py` writes a separate compatibility corpus. Its output is evidence about `numeralform.compat.num2words`, never canonical CLDR evidence.
