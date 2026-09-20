# CLDR/ICU benchmark provenance

Benchmark corpora are generated from Unicode CLDR Rule-Based Number Formatting through the pinned ICU oracle described by `benchmarks/config/cldr.toml`. The reference release is CLDR 48.2.

Generated corpus data is local benchmark output under `benchmarks/data/corpora/cldr/`; it is not committed and does not vendor the CLDR repository or add CLDR/ICU to Numeralform runtime dependencies.

The new foundation policies use the CLDR 48.2 standalone/count surface where available. Basque follows Euskaltzaindia's normative vigesimal spelling, Marathi uses a reviewed native inventory, Nepali follows the pinned CLDR spelling `तिन`, and `ku` is explicitly Kurmanji/Hawar rather than Sorani. These reviewed-only mappings do not add an ICU runtime dependency.
Unicode CLDR data is available under the Unicode CLDR license. Review the applicable Unicode license and notice text before redistributing regenerated data. Manifests record oracle and release provenance.
