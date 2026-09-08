# Locale capability inventory

The pinned compatibility scope contains 63 upstream locale codes plus the
Numeralform-only `pt-PT` registration. Capability truth is generated from the
registry and compatibility corpus rather than maintained as a hand-edited
boolean. Regional renderers are independent strategies, not aliases:
`en-IN`, `fr-BE`, and `fr-CH` have distinct number composition.

## Executable base renderers

`cs`, `de`, `en`, `es`, `fi`, `fr`, `it`, `ja`, `ko`, `pt`, `ru`, `sv`, `th`,
and `vi` have locale-owned renderers. `en-IN`, `fr-BE`, and `fr-CH` use
regional subclasses. Other regional registrations use their base renderer only
where the review found no composition difference.

## Executable baseline registrations

The remaining upstream codes are registered with a strict typed baseline
renderer so discovery and request handling are truthful rather than pretending
that a placeholder is a supported renderer. Their lexical and grammar output
is intentionally marked for locale-specific review in `capabilities()` and in
the generated compatibility status report. A locale may only widen morphology
or claim byte-for-byte compatibility after native-reviewed fixtures and oracle
cases are added.

The canonical forms and compatibility forms are independent contracts; an
upstream string does not define canonical linguistic truth.
