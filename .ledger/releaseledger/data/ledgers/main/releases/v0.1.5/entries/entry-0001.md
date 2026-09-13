---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 1
entry_id: entry-0001
release_version: v0.1.5
kind: changed
summary:
  Improved locale-aware decimal rendering and Italian currency support while
  preserving compatibility behavior
status: accepted
audience: null
scopes: []
source_refs:
  - git:db047bf984f840f52d47aea163699cdd611db1bd
paths:
  - docs/api.md
  - docs/compatibility.md
  - numeralform/compat/num2words.py
  - numeralform/currency/__init__.py
  - numeralform/renderers/_shared.py
  - tests/test_compatibility.py
  - tests/test_currency_api.py
  - tests/test_decimal_localization.py
  - tests/test_spokenform_contract.py
issues: []
prs: []
sources:
  - git:db047bf984f840f52d47aea163699cdd611db1bd
contributors: []
breaking: false
internal: false
order: 1
---
