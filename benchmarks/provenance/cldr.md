# CLDR/ICU benchmark provenance

Benchmark corpora are generated from Unicode CLDR Rule-Based Number Formatting through the pinned ICU oracle described by `benchmarks/config/cldr.toml`. The reference release is CLDR 48.2.

Generated corpus data is local benchmark output under `benchmarks/data/corpora/cldr/`; it is not committed and does not vendor the CLDR repository or add CLDR/ICU to Numeralform runtime dependencies.

Unicode CLDR data is available under the Unicode CLDR license. Review the applicable Unicode license and notice text before redistributing regenerated data. Manifests record oracle and release provenance.
