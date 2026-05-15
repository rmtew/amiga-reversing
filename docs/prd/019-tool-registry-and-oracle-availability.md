# PRD 019: Tool Registry and Oracle Availability

## Purpose

Add a project/workspace **Tool Registry** and structured **Tool Availability Records** for external tools used by oracle workflows.

## Dependencies

- PRD 018: Reproduction Profiles and Policy Summary.

## Scope

- Store user-local paths and discovery hints outside target metadata and the **Manual Action Log**.
- Detect built-in oracle tool ids: `vasm`, `genam`, and `vamos`.
- Report availability with status, required flag, resolved path, cheap version, discovery source, user-facing message, and executable stamp where possible.
- Stamp availability inputs into reproduction/oracle reports only for requested oracle checks.
- Surface missing required tools explicitly in UI/API/CLI.

## Requirements

- Target configuration may request oracle checks but must not store user-local tool paths.
- Discovery checks configured paths before PATH lookup.
- Status values are `available`, `missing`, `unsupported`, and `error`.
- Discovery sources include `configured_path`, `path_lookup`, `bundled`, and `not_checked`.
- Built-in GenAm oracle support requires a runnable GenAm path through `vamos`.
- Lower-level emulator dependencies behind `vamos` are treated as user installation concerns, not first-class project tools.
- Missing optional oracle tools produce oracle missing outcomes, not exactness gate failures.

## Non-Goals

- User interface for installing third-party tools.
- First-class support for lower-level emulator dependencies behind `vamos`.
- Oracle report execution; covered by PRD 020.
- Runtime tracing/equivalence; proposal 003 scope.

## Verification

- Unit tests for registry load/save, missing config, invalid paths, and PATH lookup.
- Tests using fake executable paths for available, missing, unsupported, and error cases.
- Route/CLI tests for availability payloads.
- Report-stamp tests proving only requested oracle availability is stamped.
- Web tests for visible missing-tool reasons.

## Issues

- [019-001: Tool Registry Storage](../issues/019-001-tool-registry-storage.md)
- [019-002: Oracle Tool Availability Detector](../issues/019-002-oracle-tool-availability-detector.md)
- [019-003: Tool Availability API CLI and UI](../issues/019-003-tool-availability-api-cli-and-ui.md)
- [019-004: Availability Stamping in Reports](../issues/019-004-availability-stamping-in-reports.md)
- [019-005: PRD 019 Review and Tightening](../issues/019-005-prd-019-review-and-tightening.md)
