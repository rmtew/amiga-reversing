# PRD 020: Oracle Compatibility Reports

## Purpose

Run non-gating assembler oracle workflows and report their comparison level separately from the active exactness gate.

## Dependencies

- PRD 018: Reproduction Profiles and Policy Summary.
- PRD 019: Tool Registry and Oracle Availability.

## Scope

- Add **Oracle Compatibility Report** sections for vasm and GenAm/DevPac-compatible source workflows.
- Render source for the selected assembler profile, run the configured oracle tool chain, and compare output where comparable.
- Lead each oracle result with scoped comparison labels such as `oracle.full_file_match`, `oracle.content_match`, `oracle.mismatch`, `oracle.not_comparable`, `oracle.missing`, and `oracle.not_run`.
- Include assembler acceptance, tool execution status, diagnostics, command metadata, and availability records as supporting evidence.

## Requirements

- Oracle reports never set the target exactness gate to `exact`.
- Bare `exact` remains reserved for the active **Reproduction Comparison** gate.
- vasm oracle uses the vasm assembler profile and concrete `vasm` tool availability.
- GenAm oracle uses DevPac-compatible rendering and concrete `genam` plus `vamos` availability.
- Oracle reports include stdout/stderr excerpts, command metadata, rendered source fingerprint, source profile, tool availability records, and output comparison details where possible.
- Missing required oracle tools produce `oracle.missing` for that oracle, not a reproduction gate failure.
- Not-comparable output is reported explicitly rather than folded into mismatch.

## Non-Goals

- Promoting external assemblers to exactness gates.
- Runtime execution equivalence beyond using `vamos` to run GenAm.
- User-defined oracle workflows.
- Tool registry storage; covered by PRD 019.

## Verification

- Unit tests for oracle result classification and scoped labels.
- Tests for vasm accepted/rejected/missing cases with fake tools.
- Tests for GenAm via `vamos` required-tool handling.
- Report schema tests proving oracle results are separate from gate status.
- Web tests showing oracle comparison level without calling it exact.

## Issues

- [020-001: Vasm Oracle Compatibility Run](../issues/020-001-vasm-oracle-compatibility-run.md)
- [020-002: GenAm Via Vamos Oracle Compatibility Run](../issues/020-002-genam-via-vamos-oracle-compatibility-run.md)
- [020-003: Oracle Report Schema and Labels](../issues/020-003-oracle-report-schema-and-labels.md)
- [020-004: Oracle Results in Reproduction UI](../issues/020-004-oracle-results-in-reproduction-ui.md)
- [020-005: PRD 020 Review and Tightening](../issues/020-005-prd-020-review-and-tightening.md)

