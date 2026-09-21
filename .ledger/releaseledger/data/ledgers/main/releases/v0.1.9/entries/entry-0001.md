---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 1
entry_id: entry-0001
release_version: v0.1.9
kind: added
summary:
  Added standalone cardinal rendering for 13 locales, expanding base-language
  coverage from 49 to 62
status: accepted
audience: null
scopes: []
source_refs:
  - git:d5643523233351cbd761e8a3b1f7130df3a52f3a
paths:
  - benchmarks/config/cldr.toml
  - benchmarks/provenance/cldr.md
  - docs/locales/README.md
  - docs/locales/capability-matrix.md
  - numeralform/registry.py
  - numeralform/renderers/__init__.py
  - numeralform/renderers/_foundation.py
  - numeralform/renderers/_shared.py
  - numeralform/renderers/bg.py
  - numeralform/renderers/el.py
  - numeralform/renderers/et.py
  - numeralform/renderers/eu.py
  - numeralform/renderers/ka.py
  - numeralform/renderers/ku.py
  - numeralform/renderers/lb.py
  - numeralform/renderers/ml.py
  - numeralform/renderers/mr.py
  - numeralform/renderers/ne.py
  - numeralform/renderers/sq.py
  - numeralform/renderers/sw.py
  - numeralform/renderers/ur.py
  - tests/test_new_spokenform_foundation_locales.py
issues: []
prs: []
sources:
  - git:d5643523233351cbd761e8a3b1f7130df3a52f3a
contributors:
  - "@holgern"
breaking: false
internal: false
order: 1
---
