# Migrate Assembler View To Canonical Forms

Status: Ready for agent
Parent PRD or proposal: `docs/prd/024-m68k-canonical-form-model.md`
Type: AFK
Blocked by: None

## Scope

Make assembler metadata a generated tool view over canonical form ids and add generated resolver aids.

## Out of scope

- Full corpus sample-plan migration.
- Simulator/effect migration.

## Files likely touched

- `src/scripts/`
- `src/generated/m68k_asm_tables.*`
- `src/m68k_assembler.c`
- `tests/`

## Acceptance criteria

- [ ] Assembler forms reference canonical form ids.
- [ ] Assembler resolution can use generated mnemonic-to-form ranges or equivalent generated candidate tables.
- [ ] Encoder rows are reached through canonical form identity.
- [ ] Whole-form runtime scans are removed or limited to temporary code with a deletion point.

## Required tests

- [ ] Test source resolve -> canonical form id -> encoder row.
- [ ] Test representative existing assembler cases still encode correctly.

## Cleanup / deletion

- Delete assembler-only form identity after callers migrate.

## Notes for agents

Prefer direct generated lookup aids over runtime rediscovery of form grouping.
