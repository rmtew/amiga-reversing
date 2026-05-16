# Classify Deferred Unsupported Families

Status: Ready for agent
Parent PRD or proposal: `docs/prd/025-m68k-generated-sample-plans-and-strict-coverage.md`
Type: AFK
Blocked by: `docs/issues/025-003-rewrite-corpus-generator-around-sample-plans.md`

## Scope

Represent MOVE16, FSAVE/FRESTORE, remaining PMMU, and generic coprocessor gaps as structured unsupported inventory in canonical coverage before canonical strict coverage checks are enabled.

## Out of scope

- Implementing those families.
- Modifying external oracles.

## Files likely touched

- `src/scripts/`
- `src/generated/`
- `tests/`

## Acceptance criteria

- [ ] Each deferred family has a structured reason tied to missing schema, sample plan, generated semantics, decode/render metadata, or oracle support.
- [ ] Each entry has a stale condition that fails strict coverage once the reason stops applying.
- [ ] Decode sample gaps and asm/decode parity gaps are not mislabeled as deferred family cleanup unless the whole family is explicitly unsupported.
- [ ] This inventory is available to `docs/issues/025-005-enable-canonical-strict-coverage-checks.md`.

## Required tests

- [ ] Test current deferred families are classified when present.
- [ ] Test stale unsupported reason failure.
- [ ] Test an asm/decode parity mismatch remains a strict failure.

## Cleanup / deletion

- Delete unsupported entries as future parser/schema/sample/metadata work implements each family.

## Notes for agents

Unsupported inventory is data, not a skip comment.
