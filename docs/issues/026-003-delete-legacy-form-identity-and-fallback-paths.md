# Delete Legacy Form Identity And Fallback Paths

Status: Ready for agent
Parent PRD or proposal: `docs/prd/026-m68k-tool-replacement-and-unsupported-closure.md`
Type: AFK
Blocked by: `docs/issues/026-002-generate-family-alias-and-render-metadata.md`

## Scope

Remove old split form identity, fallback scans, runtime joins, and diagnostic paths made obsolete by canonical generated metadata.

## Out of scope

- New coverage features.
- Unsupported-family implementation.

## Files likely touched

- `src/`
- `src/generated/`
- `src/scripts/`
- `tests/`

## Acceptance criteria

- [ ] Assembler-only and disassembler-only form identities are deleted or reduced to generated tool view rows.
- [ ] Runtime joins from disassembler-private forms back to assembler forms are gone.
- [ ] Runtime whole-form scans by mnemonic and operand shape are gone from normal paths.
- [ ] Runtime disassembler specificity scoring is gone when generated ordering and ambiguity checks replace it.
- [ ] Bootstrap diagnostic manifest is deleted or folded into canonical reporting.
- [ ] Canonical strict coverage still passes after legacy fallback deletion.

## Required tests

- [ ] Run assembler, disassembler, parity, and strict coverage tests after fallback deletion.
- [ ] Add regression tests for any removed fallback path that previously masked bad metadata.

## Cleanup / deletion

- This issue is primarily deletion. Do not retain compatibility shims unless a later issue explicitly depends on them with a removal date.

## Notes for agents

This repo has no external compatibility contract for these internal generated-table APIs.
