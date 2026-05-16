# Bootstrap Unsupported Inventory

Status: Ready for agent
Parent PRD or proposal: `docs/prd/023-m68k-diagnostic-coverage-manifest.md`
Type: AFK
Blocked by: None

## Scope

Add a small structured bootstrap inventory for intentionally unsupported current families and stale-reason checks.

## Out of scope

- Final unsupported inventory ownership in the canonical model.
- Implementing MOVE16, FSAVE/FRESTORE, PMMU, or generic coprocessor support.

## Files likely touched

- `src/scripts/`
- `tests/`

## Acceptance criteria

- [ ] Unsupported entries include form or family identity, reason, and stale condition.
- [ ] MOVE16, FSAVE/FRESTORE, remaining PMMU, and generic coprocessor gaps are represented if present in current metadata.
- [ ] Strict mode fails when an unsupported entry becomes stale.
- [ ] Diagnostic manifest deletion criteria remain documented.

## Required tests

- [ ] Test stale unsupported reason failure.
- [ ] Test an explicitly unsupported form does not appear unclassified.

## Cleanup / deletion

- Move inventory ownership into the **Canonical Form Model** in PRD 025 or PRD 026.

## Notes for agents

Unsupported means explicit missing schema, generated semantics, oracle support, or deliberately deferred family work.
