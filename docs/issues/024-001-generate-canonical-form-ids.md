# Generate Canonical Form IDs

Status: Ready for agent
Parent PRD or proposal: `docs/prd/024-m68k-canonical-form-model.md`
Type: AFK
Blocked by: `docs/issues/023-003-add-diagnostic-coverage-report-and-strict-mode.md`

## Scope

Generate the first shared canonical form table with nonzero form ids, dense row mappings, and typed id/row/operand-slot handles.

## Out of scope

- Migrating every runtime consumer.
- Generated sample plans.

## Files likely touched

- `src/scripts/`
- `src/generated/`
- `src/`
- `tests/`

## Acceptance criteria

- [ ] Generated canonical form ids are nonzero and unique.
- [ ] Dense row zero remains a valid storage row and is not used as "no form".
- [ ] Public generated headers expose distinct form id, form row, and operand slot concepts.
- [ ] Generated mapping functions or tables convert id to row and row to id.

## Required tests

- [ ] Test canonical form id uniqueness.
- [ ] Test id-to-row and row-to-id mappings.
- [ ] Test sentinel separation for form id, row, and operand slot.

## Cleanup / deletion

- None yet; this is the base for later deletion.

## Notes for agents

Use generated facts from the KB. Do not hardcode M68K instruction knowledge downstream.
