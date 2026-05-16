# Build Diagnostic Form Inventory

Status: Ready for agent
Parent PRD or proposal: `docs/prd/023-m68k-diagnostic-coverage-manifest.md`
Type: AFK
Blocked by: None

## Scope

Create a report-only diagnostic manifest that lists current generated assembler forms, disassembler forms, matched forms, asm-only forms, and disasm-only forms.

The diagnostic report must be exposed through:

```powershell
uv run python -m amiga_reversing.tools.m68k_coverage report --phase diagnostic
```

## Out of scope

- Canonical form model generation.
- Strict coverage gating.
- Tool API rewrites.

## Files likely touched

- `src/scripts/`
- `src/generated/`
- `tests/`

## Acceptance criteria

- [ ] `uv run python -m amiga_reversing.tools.m68k_coverage report --phase diagnostic` can build the diagnostic inventory from current generated metadata.
- [ ] The inventory includes assembler form count, disassembler form count, matched count, asm-only count, and disasm-only count.
- [ ] Each inventory entry has enough identity data to diagnose the mismatch.
- [ ] The implementation is documented as temporary bootstrap code.

## Required tests

- [ ] Test that the current generated tables produce non-empty assembler and disassembler inventories.
- [ ] Test that unmatched forms are reported rather than dropped.

## Cleanup / deletion

- Delete this path once canonical-model reporting replaces it.

## Notes for agents

Do not create a second durable form identity model. This is a measuring tool over current generated tables.
