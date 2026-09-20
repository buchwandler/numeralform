---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 1
entry_id: entry-0001
release_version: v0.1.8
kind: changed
summary:
  Changed locale rendering for decimal, currency, ordinal, and number edge
  cases
status: accepted
audience: null
scopes: []
source_refs:
  - git:1e6924df38ca1cc66923bca8afc8a10595ea7787
  - git:3c6351cba25af786e5b1f281a7eb453e3fce0945
paths:
  - numeralform/compat/num2words.py
  - numeralform/renderers/_shared.py
  - numeralform/renderers/ordinal.py
  - numeralform/renderers/zh.py
  - numeralform/renderers/ar.py
  - numeralform/renderers/he.py
  - numeralform/renderers/mn.py
  - tests/test_decimal_localization.py
  - tests/test_decimal_policy_invariants.py
  - tests/test_regressions.py
  - tests/test_seed109_locale_regressions.py
issues: []
prs: []
sources:
  - git:1e6924df38ca1cc66923bca8afc8a10595ea7787
  - git:3c6351cba25af786e5b1f281a7eb453e3fce0945
contributors: []
breaking: false
internal: false
order: 1
---
