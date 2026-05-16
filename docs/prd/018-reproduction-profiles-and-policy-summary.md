# PRD 018: Reproduction Profiles and Policy Summary

## Purpose

Add built-in **Reproduction Profiles** that expose target **Reproduction Policy** clearly in the UI, API, and CLI without changing exactness semantics.

## Status

Implemented. Built-in profile selection now writes concrete target reproduction options, exposes API/CLI flows, and renders policy summaries in the Web UI reproduction panel.

## Dependencies

- PRD 013: UI Preference State and Entrypoint Open.

## Scope

- Define built-in profile ids for the current exact framework gate, vasm source oracle, GenAm/DevPac-compatible source oracle, and content-semantic comparison workflow.
- Persist selected target policy as concrete reproduction options, with optional profile id for provenance and display.
- Show selected mode, assembler, backend, CPU, comparison level, requested oracles, and stale state in the reproduction panel.
- Validate profile and policy edits against the typed sets in `reproduction.py`.
- Expose profile selection as a **Target Tooling Command** through UI/API/CLI.

## Requirements

- Built-in profiles are project-provided; user-defined profiles are out of scope.
- Selecting a profile writes concrete target reproduction configuration and invalidates stale reproduction reports.
- Reports stamp the concrete policy options used, not only the profile id.
- `our` remains the only exactness assembler gate.
- `source-vasm` and `source-devpac`/GenAm profiles are oracle workflows, not exactness gates.
- Last selected profile view may be stored in **UI Preference State**, but policy authority lives in target configuration.
- Profile selection does not append to the **Manual Action Log** and does not affect review state until **Round-Trip Verification** runs.

## Non-Goals

- User-defined profile authoring.
- Tool path configuration; covered by PRD 019.
- Oracle execution/reporting; covered by PRD 020.
- Source export; covered by PRD 021.

## Verification

- Unit tests for built-in profile expansion into concrete reproduction options.
- Tests for invalid profile ids and invalid option values.
- Route/CLI tests for reading and updating active policy.
- Web tests for profile summary display and stale report state.
- Regression test proving oracle profile selection cannot mark the exactness gate `exact`.

Implemented verification:

- Unit tests cover built-in profile expansion, strict option validation, and input-stamp policy stamping.
- Route and CLI tests cover list/show/set and prove profile changes do not write the Manual Action Log.
- CDP coverage verifies command-palette profile selection and reproduction-panel stale summary display.
- `src\precommit.bat` is the final commit gate.

## Issues

- [018-001: Built-In Reproduction Profile Registry](../issues/018-001-built-in-reproduction-profile-registry.md)
- [018-002: Reproduction Policy Persistence and Validation](../issues/018-002-reproduction-policy-persistence-and-validation.md)
- [018-003: Reproduction Profile Summary UI](../issues/018-003-reproduction-profile-summary-ui.md)
- [018-004: Reproduction Profile Target Tooling Commands](../issues/018-004-reproduction-profile-target-tooling-commands.md)
- [018-005: PRD 018 Review and Tightening](../issues/018-005-prd-018-review-and-tightening.md)
