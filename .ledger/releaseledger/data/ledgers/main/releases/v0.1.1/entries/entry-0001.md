---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 1
entry_id: entry-0001
release_version: v0.1.1
kind: added
summary: Added executable rendering for 49 language families and exact regional locales
status: accepted
audience: null
scopes: []
source_refs:
  - git:e30545b649a946b48c7ddb36a9ca61ff2e6056ae
paths:
  - README.md
  - docs/locales/README.md
  - docs/locales/capability-matrix.md
  - numeralform/compat/_num2words/registry.py
  - numeralform/compat/num2words.py
  - numeralform/registry.py
  - numeralform/renderers/__init__.py
  - numeralform/renderers/_fixtures.py
  - numeralform/renderers/_shared.py
  - numeralform/renderers/ko.py
  - numeralform/renderers/zh.py
  - tests/test_capabilities.py
  - tests/test_docs.py
  - tests/test_rendering.py
  - tests/test_spokenform_contract.py
issues: []
prs: []
sources:
  - git:e30545b649a946b48c7ddb36a9ca61ff2e6056ae
contributors: []
breaking: false
internal: false
order: 1
---

Added decimal, ordinal, year, and compatibility rendering across the expanded locale inventory
