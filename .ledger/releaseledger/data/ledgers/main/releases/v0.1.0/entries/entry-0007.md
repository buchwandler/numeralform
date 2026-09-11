---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 2
entry_id: entry-0007
release_version: v0.1.0
kind: fixed
summary:
  Fixed structured currency ownership, locale capability checks, and canonical
  request validation
status: accepted
audience: null
scopes: []
source_refs:
  - git:bb266647f610588bbc1341afc1dfe51302f5b784
  - tl:task-0018
paths:
  - numeralform/currency/__init__.py
  - numeralform/model.py
  - numeralform/locale.py
  - numeralform/errors.py
  - tests/test_currency_api.py
  - tests/test_compat_hardening.py
issues: []
prs: []
sources: []
contributors: []
breaking: false
internal: false
order: 7
---

Currency values now preserve embedded codes and scales, invalid requests use package error types, capability queries follow executable locale resolution, and the typed public API is covered by hermetic regression tests.
