---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 1
entry_id: entry-0003
release_version: v0.1.0
kind: added
summary:
  Added morphology, locale features, currency, ordinal, and regional rendering
  with strict unsupported-request handling
status: accepted
audience: null
scopes: []
source_refs:
  - git:819936c0b4affe23b93867a6c6c4de7665186c25
  - git:bcab274acc238d2c09cbcaec58d4b86e7411c303
paths:
  - numeralform/model.py
  - numeralform/locale.py
  - numeralform/currency
  - numeralform/renderers/ordinal.py
  - numeralform/renderers/regional.py
  - numeralform/compat/num2words.py
  - docs/compatibility.md
  - docs/morphology.md
issues: []
prs: []
sources: []
contributors: []
breaking: false
internal: false
order: 3
---
