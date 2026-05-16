# Generate Operand Sample Registry

Status: Ready for agent
Parent PRD or proposal: `docs/prd/025-m68k-generated-sample-plans-and-strict-coverage.md`
Type: AFK
Blocked by: `docs/issues/024-001-generate-canonical-form-ids.md`

## Scope

Generate reusable sample data for non-EA operand kinds from the KB or parser-asserted KB entries.

## Out of scope

- EA family expansion.
- Corpus generator rewrite.

## Files likely touched

- `src/scripts/kb/`
- `src/scripts/`
- `knowledge/m68k_instructions.json`
- `tests/`

## Acceptance criteria

- [ ] Special operand kinds currently sampled in corpus code have generated sample entries where schema support exists.
- [ ] Parser-asserted entries include citations and rationale when PDF facts are implied but not directly parsed.
- [ ] Missing operand schemas are reported as missing sample strategy or unsupported inventory, not guessed downstream.

## Required tests

- [ ] Test generated samples for representative special operands such as control register and register-pair operands.
- [ ] Test missing schema produces explicit non-sampleable status.

## Cleanup / deletion

- Delete corresponding corpus-local operand sample rules after issue 025-003 consumes the registry.

## Notes for agents

Follow the project rule: fix parser/schema upstream, not corpus code downstream.
