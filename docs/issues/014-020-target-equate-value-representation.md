Status: Completed
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md
Parent issue: docs/issues/014-009-equate-constant-editing.md

Scope:
Add target-local EQU definition value representation separate from numeric
value and separate from immediate use-site representation.

Accepted review state:
EQU definition value representation remains display-only. EQU identity,
symbolic use-site binding, and `constant_or_equ` provenance are separate
semantic/equate decisions.

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
- Post-`014-022` split: EQU definition value representation stays
  presentation-only. EQU identity/use-site binding or `constant_or_equ`
  provenance evidence must be owned by the semantic/equate or provenance action,
  not by this display-style action.

Acceptance criteria:
- Manual replay reloads target-equate value representation exactly.
- Command execution appends the durable action and reports authoritative local
  effects.
- Render verifier checks the requested `EQU` definition value text.
- Rename/remove target-equate behavior still updates or prunes symbolic use
  sites correctly.
- Changing EQU definition display style does not create or alter provenance
  evidence, semantic hints, or type-flow descendants.
- Source identity/display boundary:
  EQU value rendering is display-only. EQU identity, symbolic use-site binding,
  and `constant_or_equ` provenance are separate semantic/equate decisions.
  A display-style action may read references to preview impact, but it cannot
  create accepted provenance or own semantic descendants.
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
- Loop verification now rejects sparse representation payloads before reload
  matching: `target.equate.represent` must carry `name`, `value`, and
  `value_representation`, and symbolic display must also carry
  `value_expression`.
- Planner command normalization strips provenance/report fields from
  `target.equate.represent` parameters, so display-style commands cannot become
  accepted evidence or remain unsatisfied because of ignored metadata.
- Embedded `target.equate.represent` command normalization strips
  provenance/report fields from command context as well; the display action
  keeps only target scope and does not carry accepted `constant_or_equ`
  evidence.
- Implementation finding: storing unbounded expression text in every C policy
  equate slot can overflow existing stack-heavy policy tests. The C expression field is
  deliberately bounded inline storage until the broader policy struct moves
  large optional strings out of stack-resident arrays.

Cleanup / deletion:
Delete after the capability is implemented and Proposal 014 is updated with
final support state.
