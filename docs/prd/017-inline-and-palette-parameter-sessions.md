# PRD 017: Inline and Palette Parameter Sessions

## Purpose

Create reusable **Parameter Session** hosts so catalog-backed edits can happen either inside the command palette or directly on the selected listing element. Inline editing remains a UI affordance over **Manual Action Catalog** actions, not direct source-text editing.

## Status

Implemented. Catalog actions now expose schema-backed text, choice-grid, and filtered-chooser sessions for palette and inline hosts.

## Dependencies

- PRD 011: Structured Contextual Action Metadata.
- PRD 012: Command Parameter Editor.
- PRD 015: Local-First Manual Edit Application.
- PRD 018: Reproduction Profiles and Policy Summary, for active assembler/profile metadata used by label validation.
- PRD 021: Source Export Workflow, for non-manual target tooling commands that may reuse parameter-session controls.

## Scope

- Add context-specific **Interaction Schema** metadata to catalog actions.
- Render the same interaction schema in palette-hosted and inline-hosted parameter sessions.
- Support text editors for **Manual Label** and **Manual Comment**.
- Support choice-grid editors for **Manual Representation** options.
- Support filtered chooser mechanics for semantic helper actions when PRD 010/011 supply option metadata.
- Add a catalog-driven **Edit Selected Command** with default `.` binding.
- Add direct default bindings for comment edit, representation choice, and semantic interpretation.
- Add label policy metadata for local validation of name and scope under the active assembler/profile.
- Allow non-manual **Target Tooling Commands** to reuse parameter-session controls where the command has schema-like parameters.

## Requirements

- Inline editing changes user-authored text annotations or bounded catalog choices only; it never edits source text, instruction operands, or bytes directly.
- Palette-hosted sessions expand from the selected command and preserve a back stack: Escape returns to the previous palette state, and Escape again closes the palette.
- Inline-hosted sessions replace the selected rendered element with the editor in place; Escape cancels and restores the element.
- Both hosts submit the same catalog action payload and use the same validation and local-first application flow.
- Text editors support label and comment text. **Review Note** add/edit actions are PRD 016 scope and may reuse these hosts once row-level note actions exist.
- Choice grids show representation options with local preview rendered from selected element metadata and backend option metadata.
- Filtered semantic choosers show backend-provided options, support local filtering, cursor movement, default selection, local preview, cancel, and Enter commit.
- Backend owns option generation, ranking, defaults, payloads, and semantic eligibility; UI owns local rendering, filtering, navigation, and preview.
- Preview metadata uses typed preview kinds, not backend-provided HTML.
- Label editing includes name and scope when local labels are supported by the active source rendering assembler profile.
- Label validation metadata distinguishes invalid syntax, policy-disallowed local labels, reserved names, conflicts, stale/unknown validation, and commit-ready names.
- The active assembler/profile context is visible where it affects editing or validation, but profile switching is out of scope.
- Profile switching remains PRD 018 scope even if this PRD's parameter-session controls are reused for the UI.
- Parameter sessions block other manual actions until committed or cancelled; navigation that changes the target cancels the session explicitly.
- Default bindings are `.` for edit selected, `;` for comment, `r` for representation, `s` for semantic interpretation, and `F2` for label rename.

## Non-Goals

- Binary patching or direct operand-byte editing.
- Defining profile or assembler switching semantics.
- Review Note action implementation or note projection.
- Backend HTML templates.
- Async backend search for huge option sets.
- Concurrent manual edit conflict resolution beyond PRD 015 one-action-at-a-time behavior.

## Verification

- Web tests for palette-hosted and inline-hosted sessions using the same interaction schema.
- CDP tests for inline label/comment edit and palette-expanded label/comment edit.
- Tests for representation choice grid preview and commit/cancel behavior.
- Tests for semantic filtered chooser mechanics with backend-provided fixture options.
- Tests for `.` choosing the catalog-provided primary edit action or showing alternatives.
- Tests for label validation metadata, including policy-disallowed local label names.
- Regression tests proving edits submit catalog actions and do not mutate rendered source text directly.

Implemented verification:

- Focused route/source/CLI tests cover interaction schemas, catalog payloads, local effects, and source wiring.
- Focused CDP tests cover inline label/comment/representation sessions plus existing palette rename/representation flows.
- `src\precommit.bat` is the final commit gate.

## Issues

- [017-001: Interaction Schema Contract](../issues/017-001-interaction-schema-contract.md)
- [017-002: Palette Hosted Parameter Sessions](../issues/017-002-palette-hosted-parameter-sessions.md)
- [017-003: Inline Text Editors For Labels And Comments](../issues/017-003-inline-text-editors-for-labels-and-comments.md)
- [017-004: Representation Choice Grid](../issues/017-004-representation-choice-grid.md)
- [017-005: Semantic Filtered Chooser Mechanics](../issues/017-005-semantic-filtered-chooser-mechanics.md)
- [017-006: Edit Selected Command And Key Bindings](../issues/017-006-edit-selected-command-and-key-bindings.md)
- [017-007: Label Policy Validation Metadata](../issues/017-007-label-policy-validation-metadata.md)
- [017-008: PRD 017 Review And Tightening](../issues/017-008-prd-017-review-and-tightening.md)

## Follow-On PRDs

- PRD 016 may reuse PRD 017 text parameter sessions for Review Note add/edit once note actions exist.
- PRD 018 may reuse PRD 017 controls for reproduction profile selection.
- PRD 021 may reuse PRD 017 controls for source export assembler selection.
