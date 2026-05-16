# PRD 022: Full Reproduction Validation Sweep

## Purpose

Refresh full reproduction validation for GenAm and Bloodwych using the new profile/oracle reporting language.

## Dependencies

- PRD 018: Reproduction Profiles and Policy Summary.
- PRD 019: Tool Registry and Oracle Availability.
- PRD 020: Oracle Compatibility Reports.

## Status

Complete. Refreshed GenAm and Bloodwych gate reports, recorded oracle classifications, and added repeatable validation notes.

## Scope

- Re-run full reproduction validation for GenAm and Bloodwych.
- Produce fresh reports using the active exactness gate and requested oracle sections.
- Classify results as gate exact, gate content match, gate mismatch, oracle full-file match, oracle content match, oracle mismatch, not comparable, missing, or not run.
- Record classifications in report files or follow-up notes, not ad hoc console output.

## Requirements

- The sweep must not introduce new profile, policy, or tool-registry architecture.
- Report classifications use the scoped gate/oracle language from PRDs 018-020.
- Known target results are reviewable and repeatable.
- Tool-missing cases are explicit and do not mask gate failures.
- The sweep can be skipped locally only through the existing explicit integration-test opt-in/opt-out mechanisms.

## Non-Goals

- Broad corpus sweep.
- Fixing unrelated reproduction regressions discovered during the sweep.
- Runtime tracing or gameplay equivalence.

## Verification

- Integration runs for GenAm and Bloodwych with report output.
- Tests or fixtures proving classification parsing for gate and oracle sections.
- Documentation or generated report notes summarizing classifications.
- Existing full reproduction tests remain green where applicable.
- Verified with related tests, ruff, and `src\precommit.bat`.

## Issues

- [022-001: GenAm Full Reproduction Validation Refresh](../issues/022-001-genam-full-reproduction-validation-refresh.md)
- [022-002: Bloodwych Full Reproduction Validation Refresh](../issues/022-002-bloodwych-full-reproduction-validation-refresh.md)
- [022-003: Validation Classification Notes](../issues/022-003-validation-classification-notes.md)
- [022-004: PRD 022 Review and Tightening](../issues/022-004-prd-022-review-and-tightening.md)
