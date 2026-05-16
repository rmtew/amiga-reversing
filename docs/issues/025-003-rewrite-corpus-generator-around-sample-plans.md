# Rewrite Corpus Generator Around Sample Plans

Status: Ready for agent
Parent PRD or proposal: `docs/prd/025-m68k-generated-sample-plans-and-strict-coverage.md`
Type: AFK
Blocked by: None

## Scope

Make assembler corpus generation expand generated sample plans and stop owning special M68K operand knowledge.

## Out of scope

- Adding support for deferred unsupported families.
- Replacing simulator metadata.

## Files likely touched

- `src/scripts/generate_c99_assembler_corpus.py`
- `src/scripts/`
- `src/tests/generated/`
- `tests/`

## Acceptance criteria

- [ ] Corpus generation iterates canonical forms and generated sample plans.
- [ ] Non-sampleable forms record structured coverage status.
- [ ] Special operand sample choices come from generated data.
- [ ] EA sample expansion comes from generated EA plans.
- [ ] Generated corpus output remains accepted by existing assembler tests.

## Required tests

- [ ] Test corpus generation for representative normal, special-operand, and EA-family forms.
- [ ] Regenerate corpus and run affected C backend tests.

## Cleanup / deletion

- Delete corpus-local special operand guessing and detached unsupported lists.

## Notes for agents

The corpus generator should be an interpreter, not an ISA knowledge source.
