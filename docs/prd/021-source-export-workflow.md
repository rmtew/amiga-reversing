# PRD 021: Source Export Workflow

## Purpose

Add **Source Export** so users can save rendered assembler source as a `.s` file through standard browser file save, API, and CLI flows.

## Dependencies

- PRD 008: Command Palette and Default Key Bindings.
- PRD 017: Inline and Palette Parameter Sessions.
- PRD 018: Reproduction Profiles and Policy Summary.

## Scope

- Export source for a selected **Assembler Profile** such as `vasm` or `devpac`.
- Deliver Web UI exports through the standard browser save flow; the saved file is user-owned external output.
- Expose export as a **Target Tooling Command**, not a **Manual Action Catalog** action.
- Add a minimal generated header with target name, assembler profile, metadata or target identity hash, generated timestamp, and a statement that export is not verification.
- Return refusal diagnostics when source rendering refuses output.

## Requirements

- Source export can run without a round-trip or oracle run.
- Exporting source does not append to the **Manual Action Log** and does not affect review state.
- Export result is command feedback only, not persistent target status.
- The command palette may list export alongside manual and navigation commands while preserving its target-tooling semantics.
- The UI may reuse parameter-session controls for assembler profile selection.
- CLI/API exports use the same rendering path and assembler-profile validation as Web UI exports.
- Last selected export assembler may be stored in **UI Preference State**.

## Non-Goals

- Project-owned generated export artifacts or sidecar files.
- Treating export success as verification.
- Direct source-text editing.
- Oracle execution after export; covered by PRD 020.

## Verification

- Route tests for export success, selected assembler profile, and refusal diagnostics.
- Web tests for browser-delivered `.s` export and header content.
- CLI tests for source export with selected assembler profile.
- Tests proving export does not write the **Manual Action Log** or review state.
- Tests proving export command appears in the centralized palette as target tooling.

## Issues

- [021-001: Source Export Route and Browser Save](../issues/021-001-source-export-route-and-browser-save.md)
- [021-002: Source Export Assembler Profile Selection](../issues/021-002-source-export-assembler-profile-selection.md)
- [021-003: Source Export Header and Refusal Diagnostics](../issues/021-003-source-export-header-and-refusal-diagnostics.md)
- [021-004: Source Export CLI](../issues/021-004-source-export-cli.md)
- [021-005: Source Export Command Palette Integration](../issues/021-005-source-export-command-palette-integration.md)
- [021-006: PRD 021 Review and Tightening](../issues/021-006-prd-021-review-and-tightening.md)

