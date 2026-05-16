# Generate EA Family Sample Plans

Status: Ready for agent
Parent PRD or proposal: `docs/prd/025-m68k-generated-sample-plans-and-strict-coverage.md`
Type: AFK
Blocked by: None

## Scope

Generate EA sample plans by required family, covered family, CPU tier, operand role, and form.

## Out of scope

- Special non-EA operands.
- Oracle execution.

## Files likely touched

- `src/scripts/kb/`
- `src/scripts/`
- `tests/`

## Acceptance criteria

- [ ] EA sample plans distinguish register, memory, displacement, indexed, PC-relative, absolute, and immediate families where valid.
- [ ] CPU-specific EA forms are represented by CPU tier.
- [ ] Reports can list required, covered, and missing EA families per form operand.

## Required tests

- [ ] Test representative source, destination, and read/write EA roles.
- [ ] Test CPU-tier differences for 68000 and 68020+ EA families where applicable.

## Cleanup / deletion

- Delete duplicated EA-family selection from corpus code after issue 025-003.

## Notes for agents

Do not turn "one valid EA sample" into full EA-family coverage.
