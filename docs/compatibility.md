# num2words compatibility contract

Numeralform provides a separate, deterministic `num2words` compatibility namespace. The declared profile targets the upstream Git revision `07814cb114157f582c40a00119c2e9faba8dcee2`, identified as `num2words-git-07814cb`. Upstream package metadata at that revision is `0.5.14`. This is not the published `v0.5.14` tag, which is a separate compatibility product.

## Contract boundaries

- Canonical Numeralform uses BCP-47 locale resolution and reviewed capability profiles.
- The compatibility adapter preserves legacy converter-key resolution, including underscore versus hyphen behavior.
- Compatibility-only renderers do not change `locales()`, `known_locales()`, or `supports()` for the canonical API.
- The runtime adapter never imports or delegates to an installed upstream package.
- The upstream package is used only as an external oracle while generating behavioral data and running the optional upstream test shim.
- Generated outputs are behavioral test data. LGPL implementation source is not copied into this Apache-2.0 project.

## Reproducible generation

`compatibility.toml` records the profile, repository, exact revision, package metadata, locale scope, forms, and generation profiles. Generation must use a checkout whose `git rev-parse HEAD` equals the configured revision:

```bash
python tools/validation/generate_num2words.py \
  --config compatibility.toml \
  --oracle-root .upstream-num2words \
  --output tests/validation/compatibility/num2words-git-07814cb.jsonl
python tools/validation/generate_num2words.py \
  --config compatibility.toml \
  --oracle-root .upstream-num2words \
  --output tests/validation/compatibility/num2words-git-07814cb.jsonl \
  --check
```

The manifest stores both the source revision and package version metadata. Site-packages is not accepted when `--oracle-root` is supplied. The corpus checker is offline and validates JSONL ordering, NFC output, file hashes, case counts, exception records, and compatibility mismatch dimensions.

## Legacy language selection

Legacy converter keys use underscores, such as `en_IN`, `fr_CH`, and `zh_CN`. An input such as `en-IN`, `fr-CH`, or `zh-CN` is not converted to an underscore key before resolution. It falls back to the two-character language key, matching the upstream API. This intentionally differs from canonical BCP-47 behavior.

## Compatibility superset

The adapter also preserves selected Numeralform extensions, including fraction strings, precision handling, variable currency scales, and richer cents behavior. These extensions are compatibility-superset behavior, not claims about the upstream API.
