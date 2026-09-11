---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 4
entry_id: entry-0004
release_version: v0.1.0
kind: quality
summary:
  Improved release benchmark validation with pinned corpora and randomized
  differential gates
status: accepted
audience: null
scopes: []
source_refs:
  - git:e74b7038f4af7a21df6cdeeb9267a7072d20818a
  - git:55aab067feca7a22fea6a742fd386823ae11c091
  - git:5cd19e8b860a36f395938a80b785a9dcbef7bded
  - git:3ca66a4daf62bf0f0f48ed0e1876b3605149ff54
  - git:1fcd9a82cc3225edc624c83c48ba353b20a296ae
  - git:3234ab289a86789278aa1486342888cc019c560b
  - git:a0bf9efe65c3f7839c6244279ee5d5f269144240
  - git:64afaef1cfcdd36d0ae69459fd2e98479b170337
  - git:e2f040037e05bca4f1392b0ed43d026f8120e5cc
  - git:d38c2ab2e61d900b507dcee3c389dfe855e89cfe
  - git:0f77771f7a8007eb1850d44689cd66c86c7ce15e
paths:
  - benchmarks/README.md
  - benchmarks/validation
  - benchmarks/tests
issues: []
prs: []
sources: []
contributors: []
breaking: false
internal: false
order: 4
---

Benchmark data and reports are isolated under benchmarks/data; framework tests and external-oracle gates run separately from hermetic product tests.
