Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Define durable target identities for every editable source-converging construct
identified by 014-001.

Accepted review state:
Identity work may proceed alongside `014-010`. First implementation support
should cover `source_evidence_id`, `owner_action_id`, accepted evidence status,
and explicit path/lifetime scope for register/base provenance reports.

Out of scope:
Do not add UI-only or agent-only identifiers. Do not rely on row index, row
text, DOM text, or screenshots.

Files likely touched:
- listing locator and element identity code
- manual action/catalog identity helpers
- source rendering/projection tests
- proposal matrix

Acceptance criteria:
- Each editable construct has a stable identity contract.
- Identities survive projection rebuilds and can be used by Manual Action Log
  replay, command discovery, command execution, and verification.
- Derived analysis facts carry enough ownership identity to be recomputed or
  retracted when their source manual action or source fact is removed.
- Missing identity support is broken into implementation issues.

Current observations:
- `suppress_seeded_item` uses the durable tuple `(kind, hunk, addr)` for
  Manual Action Log replay and effective metadata projection.
- Listing and command row contexts now surface suppressible
  `target_seeded_metadata.json` entries with `(kind, hunk, addr)` plus source
  id/path/locator provenance, which is enough for seeded-item suppression
  commands.
- Listing element identity preserves operand index `0` for selected operands,
  app slots, typed accesses, and typed gaps instead of treating it as absent.
- Command mutation metadata preserves row index `0` when reporting label local
  effects and pending analysis ranges.
- Data-block layout identity is now defined by the `014-015` investigation:
  source-backed layouts use target, hunk, source range, and layout id;
  runtime-backed layouts also include source/origin execution-view identity;
  elements use layout id plus offset. Implementation belongs in
  `014-016-data-block-layout-core-metadata.md`, with command-specific use in
  `014-017` through `014-019`.
- RSSET numeric use-site binding identity is now defined by the `014-021`
  investigation: target, hunk, source address, operand index, base register,
  displacement, chosen `(layout_name, base_symbol)`, and base-evidence id.
  Implementation belongs in `014-011`; identity helpers must preserve operand
  index `0` and must not use row index or rendered text as identity.
- Manual Action Log records already persist stable `action_id` values, reject
  duplicate ids during replay, and expose active/inactive action ids after
  undo/redo projection. RSSET binding cleanup can use those ids as
  `owner_action_id`; no separate owner-id prerequisite is needed unless a
  future cascade needs ids for non-MAL source facts.
- Derived analysis facts need ownership identity too. Xrefs, type-flow facts,
  review items, symbolic projections, and other descendants of a manual action
  must be attributable to the source manual action or source fact so corrective
  actions can retract only those descendants.
- This ownership requirement applies to semantic/type-producing actions, not to
  purely presentational edits. Label renames, comments, and literal
  representation choices do not need cascade identity unless they also create
  semantic analysis facts. Type assignments, register/base seeds, RSSET
  bindings/refinements, struct/platform field bindings, interpreted references,
  and API/register semantic actions must carry enough evidence and owner
  identity to reconcile with existing analysis and retract generated descendants.
- The post-`014-022` model treats generic provenance/def-use evidence as a
  reusable cross-cutting identity source. Durable semantic/type descendants may
  need both `source_evidence_id` for the accepted provenance/classification and
  `owner_action_id` for the specific field/bind/type action that generated the
  projection.
- `source_evidence_id` should be an opaque stable id derived from a normalized
  evidence identity, not row text or row index. First-slice register/base ids
  should encode source family, target, hunk, subject source address, operand
  index when present, register/base register, origin kind, origin hunk/offset
  when known, and path/lifetime scope. Manual classifications and overrides may
  use the persisted Manual Action Log `action_id` as the stable suffix.
- `owner_action_id` is the persisted Manual Action Log action id for the edit
  that created generated descendants. It is separate from
  `source_evidence_id`: many bindings/type edits can consume the same accepted
  evidence, and one binding/type edit can generate many owned descendants.
- Path/lifetime scope identity must be explicit when a definition is not
  globally valid. Use normalized scopes such as entry, source range, defining
  instruction to clobber, caller/callee context, selected CFG path, or manually
  chosen scope. Conflicting/path-specific evidence must not collapse to a
  target-wide id.
- Evidence statuses are part of identity validation: `analysis_proven`,
  `path_specific`, `conflicting`, `unknown`, `unresolved`,
  `manual_classified`, `manual_override`, and future analyzer-bug/retracted
  states. Generated descendants must store the accepted status they consumed,
  or verifier cleanup cannot distinguish stale projections from still-valid
  facts.
- Generated descendants such as selected-use symbols, xrefs, linked gaps,
  same-displacement candidates, review items, and type-flow facts must carry
  both consumed `source_evidence_id` and generating `owner_action_id` whenever
  those are different.
- First-slice provenance reports now generate stable opaque
  `source_evidence_id` values from target, source family, status, hunk/source
  address, operand index, register/base register, displacement when present,
  origin kind, all parent evidence ids when they exist, and the complete
  normalized path/lifetime scope. These ids are report evidence only until an
  accepted classification or family-specific bind/type action records them
  durably.
- Path/lifetime scope identity now uses the full normalized scope payload, not
  only the scope kind, so two same-subject path-specific definitions with
  different selected CFG paths or caller/callee contexts do not collapse to one
  report evidence id.
- Command execution preserves target identity into selected element context, so
  catalog-derived evidence ids do not fall back to target-agnostic ids after
  locator re-selection.
- Review-item/reproduction correction identities beyond seeded-item row
  suppression still need specific contracts.

Required tests:
Focused identity/locator tests for any new identity contracts.

Cleanup / deletion:
Delete after all required identity gaps are either implemented or split into
specific issues.
