# Generate Family Alias And Render Metadata

Status: Ready for agent
Parent PRD or proposal: `docs/prd/026-m68k-tool-replacement-and-unsupported-closure.md`
Type: AFK
Blocked by: `docs/issues/024-001-generate-canonical-form-ids.md`

## Scope

Move mnemonic family, condition-code family, size suffix, alias, and render-family facts into generated metadata.

## Out of scope

- Formatting changes unrelated to generated metadata.
- New instruction-family implementation.

## Files likely touched

- `src/scripts/`
- `src/generated/`
- `src/m68k_ir_codec.c`
- `src/m68k_render_ir.c`
- `tests/`

## Acceptance criteria

- [ ] Generated metadata exposes branch, DBcc, Scc, TRAPcc, size-suffix, alias, and render-family facts.
- [ ] IR codec and renderer consumers use generated metadata.
- [ ] Handwritten downstream switch lists are removed from the tested path.
- [ ] Existing conditional, branch, trap, and alias behavior remains correct.

## Required tests

- [ ] Test generated family metadata for representative conditional families.
- [ ] Test size suffix behavior is table-driven.
- [ ] Test alias/render behavior through observable rendered or encoded output.

## Cleanup / deletion

- Delete mnemonic-family and size-suffix switch helpers replaced by metadata.

## Notes for agents

If a fact is missing, add it to the parser/schema/canonical model instead of recreating a C switch.
