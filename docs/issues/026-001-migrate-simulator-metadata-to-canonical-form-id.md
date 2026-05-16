# Migrate Simulator Metadata To Canonical Form ID

Status: Ready for agent
Parent PRD or proposal: `docs/prd/026-m68k-tool-replacement-and-unsupported-closure.md`
Type: AFK
Blocked by: `docs/issues/024-001-generate-canonical-form-ids.md`

## Scope

Make simulator/effect metadata lookup use canonical form id and generated semantic status.

## Out of scope

- Implementing missing instruction semantics.
- Runtime tracing changes.

## Files likely touched

- `src/scripts/`
- `src/generated/`
- `src/m68k_simulator.c`
- `src/test_m68k_simulator.c`

## Acceptance criteria

- [ ] Simulator/effect lookup is keyed by canonical form id.
- [ ] Forms without generated semantics return `generated_semantics_missing` or equivalent structured status.
- [ ] Lookup no longer falls back to mnemonic plus operand shape.
- [ ] Existing simulator tests pass for supported forms.

## Required tests

- [ ] Test supported form lookup by canonical form id.
- [ ] Test missing generated semantics status.
- [ ] Test absence of fallback lookup in the tested path.

## Cleanup / deletion

- Delete simulator fallback lookup by mnemonic and expected operand kind.

## Notes for agents

Downstream executor code must consume generated facts or report missing generated semantics.
