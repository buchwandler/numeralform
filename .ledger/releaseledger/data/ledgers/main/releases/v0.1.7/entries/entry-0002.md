---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 1
entry_id: entry-0002
release_version: v0.1.7
kind: fixed
summary:
  Fixed compatibility ordinal rendering for locale-specific spellings, morphology,
  and supported ranges
status: accepted
audience: null
scopes: []
source_refs:
  - git:d902413441065fbbf0e62ac9946c3a8773b35fae
paths:
  - .github/workflows/benchmarks.yml
  - benchmarks/config/num2words_random.toml
  - benchmarks/randomized/adapters.py
  - benchmarks/randomized/generator.py
  - benchmarks/randomized/oracle.py
  - benchmarks/randomized/run.py
  - benchmarks/tests/test_randomized_adapters.py
  - benchmarks/tests/test_randomized_generator.py
  - benchmarks/tests/test_randomized_runner.py
  - numeralform/compat/num2words.py
  - numeralform/renderers/_shared.py
  - numeralform/renderers/es.py
  - numeralform/renderers/pt.py
  - numeralform/renderers/zh.py
  - tests/test_regressions.py
issues: []
prs: []
sources:
  - git:d902413441065fbbf0e62ac9946c3a8773b35fae
contributors:
  - "@holgern"
breaking: false
internal: false
order: 2
---
