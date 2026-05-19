Status: Completed
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md
Parent issue: docs/issues/014-009-equate-constant-editing.md

Scope:
Add target-local EQU definition value representation separate from numeric
value and separate from immediate use-site representation.

Problem:
`014-009` made target-local equates source-converging for identity, CRUD, and
symbolic use sites. It does not let the user or reversing loop choose how an
EQU definition value itself renders. For recovered source, `$20`, `%00100000`,
`32`, and `' '` can communicate different intent while preserving the same
numeric value.

Requirements:
- Add durable metadata for target-equate value representation: hex, decimal,
  binary, character, or symbolic expression.
- Keep numeric value semantics separate from display style.
- Expose command catalog support for changing an EQU definition representation
  without private loop-only paths.
- Replay through Manual Action Log and effective metadata.
- Render the requested `EQU` value text while preserving exact rebuild.
- Compose with data-block element enum/equate domains from `014-019` without
  copying per-use-site strings.
- Treat definition value representation as display metadata only: it must not
  change numeric equate semantics, use-site bindings, or auto-analysis facts.

Acceptance criteria:
- Manual replay reloads target-equate value representation exactly.
- Command execution appends the durable action and reports authoritative local
  effects.
- Render verifier checks the requested `EQU` definition value text.
- Rename/remove target-equate behavior still updates or prunes symbolic use
  sites correctly.
- Exact direct rebuild remains mandatory.

Required tests:
Manual replay, command catalog execution, rendered `EQU` definition text,
rename/remove regression, loop verifier, and exact rebuild tests.

Implemented support:
- `TargetEquateMetadata` and Manual Action Log replay preserve optional
  `value_representation` and `value_expression` fields while keeping `value` as
  the numeric semantic source of truth.
- The command catalog exposes `target.equate.represent` through the same durable
  target-equate payload path as add/edit, with authoritative local effects.
- The C policy parser/exporter and source renderer now render hex, decimal,
  binary, character, and bounded symbolic-expression definition text.
- Exact direct rebuild remains the verifier for symbolic-expression correctness;
  changing definition display does not create provenance, semantic hints, or
  type-flow descendants.
- Implementation finding: storing unbounded expression text in every C policy
  equate slot can overflow existing stack-heavy policy tests. The C expression field is
  deliberately bounded inline storage until the broader policy struct moves
  large optional strings out of stack-resident arrays.

Cleanup / deletion:
Delete after the capability is implemented and Proposal 014 is updated with
final support state.
