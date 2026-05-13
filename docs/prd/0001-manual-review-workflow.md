# PRD 0001: Manual Review Workflow

## Problem Statement

Users who want to finish reverse-engineering work manually need a clear post-analysis workflow. Current automatic analysis can explain bytes reached from entrypoints and accepted seeds, but it does not give users a durable, navigable, replayable way to handle unreconciled ranges, suspicious decodes, reproduction problems, labels, comments, or manual conversions. The old `entities.jsonl` and `overrides.json` model mixes generated facts with user state and should be removed rather than preserved.

## Solution

Introduce a Manual Review workflow built from generated Manual Review Items and a per-target Manual Action Log. The system will keep entrypoint analysis primary, project manual user intent as Manual Seeds, Manual Labels, Manual Comments, and Manual Resolutions, and compute Review State as `clear`, `needs_review`, or `blocked`. Manual Review Items are regenerated from current analysis facts and matched to previous resolutions through stable ids and Evidence Fingerprints.

## User Stories

1. As a reverse engineer, I want unreconciled ranges surfaced as Manual Review Items, so that I can focus on work the tool could not prove.
2. As a reverse engineer, I want Review State to summarize `clear`, `needs_review`, or `blocked`, so that I can judge target readiness quickly.
3. As a reverse engineer, I want `clear` to mean no known actionable manual work remains, so that the tool does not overclaim full understanding.
4. As a reverse engineer, I want reproduction content mismatches to block review, so that I do not miss semantic rebuild failures.
5. As a reverse engineer, I want container-only differences to remain review work, so that non-semantic file shape problems do not falsely block content work.
6. As a reverse engineer, I want orphan code candidates listed with evidence, so that I can decide whether to seed code or leave data alone.
7. As a reverse engineer, I want suspicious instruction decodes flagged conservatively, so that likely misclassified code is actionable and not noisy.
8. As a reverse engineer, I want unclassified data ranges listed only when evidence is missing, so that unreferenced but valid assets are not treated as errors.
9. As a reverse engineer, I want to convert bytes to code or data through Manual Seeds, so that analysis reruns from explicit user intent.
10. As a reverse engineer, I want required Manual Seeds to conflict rather than override entrypoint-proven facts, so that manual mistakes cannot corrupt proven flow.
11. As a reverse engineer, I want suggested Manual Seeds for exploratory work, so that I can ask the tool to try a classification without forcing it.
12. As a reverse engineer, I want manual actions replayed in order, so that undo and redo can be modeled without mutating history.
13. As a reverse engineer, I want target identity checked before applying manual actions, so that stale offsets are never applied to the wrong binary.
14. As a reverse engineer, I want target identity mismatch to be fatal for the project target, so that the project must be restored or reimported.
15. As a reverse engineer, I want manual labels and comments stored as actions, so that old entity overrides are unnecessary.
16. As a reverse engineer, I want manual labels to affect rendering but not prove code or data, so that naming and classification remain separate.
17. As a reverse engineer, I want labels and comments on unreconciled ranges to create review work, so that annotations do not hide unknown bytes.
18. As a reverse engineer, I want label scopes modeled for generated and manual labels, so that future local labels can be correct.
19. As a reverse engineer, I want local label support gated by assembler profile metadata, so that source rendering does not hardcode assembler folklore.
20. As a reverse engineer, I want duplicate or invalid labels surfaced as label scope conflicts, so that emitted source stays unambiguous.
21. As a reverse engineer, I want Manual Review Items to include structured Suggested Review Actions, so that the UI can offer precise next steps.
22. As a reverse engineer, I want navigation actions kept transient, so that the Manual Action Log stores only domain-changing actions.
23. As a reverse engineer, I want a checklist-first manual review UI, so that I can process review work efficiently.
24. As a reverse engineer, I want facets for kind, confidence, section, source, state, and range, so that I can focus the checklist.
25. As a reverse engineer, I want rendering and export to show warnings for blocked targets, so that work remains possible without pretending the target is clear.
26. As a maintainer, I want `entities.jsonl` and `overrides.json` support removed, so that stale target-state models do not keep accumulating tech debt.
27. As a maintainer, I want generated facts, manual projections, and rendered source boundaries kept separate, so that each model has one job.
28. As a maintainer, I want CDP tests and precommit to gate every task, so that UI and toolchain behavior stay verified.

## Implementation Decisions

- Manual Review Items are regenerated from current analysis facts and are not durable source state.
- Manual Action Log is the durable per-target manual state. It contains a header record with version and Target Identity followed by ordered domain actions.
- Missing Manual Action Log means empty manual state. Header-only log is also empty manual state with pinned Target Identity.
- Manual Seeds, Manual Labels, Manual Comments, and Manual Resolutions are projections from the Manual Action Log.
- Undo and redo append compensating actions rather than deleting prior log entries.
- Target Identity includes original byte hash, target format or platform, section or hunk layout, runtime or load address metadata, and extracted child source identity.
- Target Identity excludes display names, notes, UI labels, generated analysis outputs, and Assembler Profile unless the profile changes address interpretation.
- Target Identity mismatch is fatal for that project target. The log is not applied and the target remains `blocked` until restored or reimported.
- Entrypoints remain primary analysis evidence. Manual Seeds augment the same analysis run with lower provenance priority.
- Seed priority is entrypoint, metadata or policy, required Manual Seed, suggested Manual Seed.
- Required Manual Seeds must be honored or create conflict review work. They do not override entrypoint-proven facts.
- Suggested Manual Seeds may be rejected when stronger evidence contradicts them.
- Manual Labels name addresses or range starts for rendering and UI. They do not prove classification unless paired with Manual Seeds.
- Manual Comments attach notes to addresses or ranges and do not prove classification.
- Label Scope applies to generated labels, metadata or policy labels, and Manual Labels.
- Local Label Scope ownership is explicit in internal facts and actions. Nearest-previous-label behavior is only an assembler emission constraint.
- Assembler Profile owns local-label support metadata such as prefix, owner rule, reserved local names, and required mode flags.
- Generated labels remain globally unique until local-label emission is proven.
- `entities.jsonl`, `overrides.json`, entity confidence, and entity verification status are removed as state models.
- Review State is `clear`, `needs_review`, or `blocked`. `blocked` prevents clear rating but is not a general UI/export lock.
- Suggested Review Actions are structured descriptors. Only domain-changing actions append to the Manual Action Log.
- Minimum v1 Suggested Review Actions are:
  - orphan code candidate: navigate, create required code Manual Seed, resolve as data or padding.
  - unreconciled data range: navigate, create data Manual Seed as string, scalar table, pointer table, or raw unit, resolve as opaque data.
  - suspicious instruction decode: navigate, create data Manual Seed, acknowledge.
  - manual label/comment unreconciled: create Manual Seed, remove annotation, acknowledge.
  - reproduction mismatch: open comparison, rerun Round-Trip Verification, acknowledge container-only difference when Content Exactness is preserved.

## Testing Decisions

- Tests should exercise external behavior: persisted actions replay to the expected projected state, analysis consumes projected state correctly, review items are regenerated correctly, and UI flows append the right actions.
- Manual Action Log projection should be tested as a deep module with small fixtures covering missing logs, header-only logs, sequence inconsistencies, undo/redo, target identity mismatch, and malformed actions.
- Manual Review Item generation should be tested from generated analysis facts and manual projections, not by asserting internal implementation details.
- Manual Seed analysis behavior should be tested with narrow binary fixtures proving entrypoint priority, required conflicts, suggested rejection, and cascade through discovered flow.
- Label Scope should be tested through rendering/assembly behavior where possible, and through profile metadata checks where local emission is not yet supported.
- UI checklist behavior should be covered by CDP tests, including creating a seed from a suggested action, resolving an item, and seeing Review State update.
- Every implementation issue must pass CDP tests and `cmd /c src\precommit.bat`.

## Issues

1. [0001-001 Manual Action Log Projection](../issues/0001-001-manual-action-log-projection.md)
2. [0001-002 Stop Requiring Legacy Entity State](../issues/0001-002-remove-legacy-entity-state.md)
3. [0001-003 Manual Seeds In Analysis](../issues/0001-003-manual-seeds-in-analysis.md)
4. [0001-004 Manual Review Item Generation](../issues/0001-004-manual-review-item-generation.md)
5. [0001-005 Manual Labels Comments And Label Scope](../issues/0001-005-manual-labels-comments-and-label-scope.md)
6. [0001-006 Checklist Review UI And Suggested Actions](../issues/0001-006-checklist-review-ui-and-suggested-actions.md)
7. [0001-007 Review State Rendering Export Warnings](../issues/0001-007-review-state-rendering-export-warnings.md)
8. [0001-008 Delete Legacy Entity Support](../issues/0001-008-delete-legacy-entity-support.md)
9. [0001-009 Target Regeneration And Cleanup](../issues/0001-009-target-regeneration-and-cleanup.md)
10. [0001-010 Keep Live Blockers Blocked](../issues/0001-010-keep-live-blockers-blocked.md)
11. [0001-011 Replay Undo Redo In File Order](../issues/0001-011-replay-undo-redo-in-file-order.md)
12. [0001-012 Reject Reserved Manual Action Fields](../issues/0001-012-reject-reserved-manual-action-fields.md)
13. [0001-013 Normalize Blocked Review State Projection](../issues/0001-013-normalize-blocked-review-state-projection.md)

## Out of Scope

- GitHub issue publication.
- Rebase or accept-identity-change flows for Manual Action Logs.
- Encouraging local labels in the v1 manual-label UI before assembler-profile support and emission checks are proven.
- Keeping compatibility with existing `entities.jsonl` or `overrides.json` state.
- Claiming `clear` means a target is fully understood.

## Further Notes

The main design references are the Manual Review Items section in the M68K analysis design notes and ADR 0004 for the Manual Action Log. Existing targets may be regenerated or reimported; there is no external compatibility requirement.
