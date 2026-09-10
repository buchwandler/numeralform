# num2words benchmark provenance

Expected compatibility strings are generated independently by the benchmark tooling from the pinned executable oracle:

- repository: `savoirfairelinux/num2words`
- commit: `07814cb114157f582c40a00119c2e9faba8dcee2`
- version: `0.5.14`
- license of the oracle and its test suite: LGPL-2.1-or-later

Numeralform does not vendor upstream implementation or test source. Generated JSONL is local behavioral evidence under `benchmarks/data/`; it does not relicense the external oracle.
