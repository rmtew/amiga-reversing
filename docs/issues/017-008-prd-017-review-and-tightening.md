# 017-008: PRD 017 Review And Tightening

## Parent

[PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Related PRDs

- [PRD 011: Structured Contextual Action Metadata](../prd/011-structured-contextual-action-metadata.md)
- [PRD 012: Command Parameter Editor](../prd/012-command-parameter-editor.md)
- [PRD 015: Local-First Manual Edit Application](../prd/015-local-first-manual-edit-application.md)
- [PRD 018: Reproduction Profiles and Policy Summary](../prd/018-reproduction-profiles-and-policy-summary.md)
- [PRD 021: Source Export Workflow](../prd/021-source-export-workflow.md)

## Type

AFK

## Labels

done

## What to build

Review inline and palette **Parameter Sessions** against PRD 017, ensuring both hosts use the same interaction schema and all edits remain catalog-backed.

## Acceptance criteria

- [x] Palette and inline hosts share interaction schema behavior.
- [x] Inline editing does not mutate source text, instruction operands, or bytes directly.
- [x] Representation and semantic choosers use backend-provided option metadata.
- [x] `.` and direct key bindings are catalog-driven.
- [x] Label validation metadata handles assembler/profile policy correctly.
- [x] Non-manual target tooling command reuse does not blur Manual Action Catalog semantics.
- [x] PRD 017 links and issue statuses remain accurate after review.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion Notes

- PRD 017 is implemented through catalog metadata, shared session rendering, and catalog execution only.
- Target-tooling reuse remains limited to schema-compatible controls; Manual Action Catalog semantics stay separate.

## Blocked by

- [017-001: Interaction Schema Contract](017-001-interaction-schema-contract.md)
- [017-002: Palette Hosted Parameter Sessions](017-002-palette-hosted-parameter-sessions.md)
- [017-003: Inline Text Editors For Labels And Comments](017-003-inline-text-editors-for-labels-and-comments.md)
- [017-004: Representation Choice Grid](017-004-representation-choice-grid.md)
- [017-005: Semantic Filtered Chooser Mechanics](017-005-semantic-filtered-chooser-mechanics.md)
- [017-006: Edit Selected Command And Key Bindings](017-006-edit-selected-command-and-key-bindings.md)
- [017-007: Label Policy Validation Metadata](017-007-label-policy-validation-metadata.md)
