# Run Final Generated Coverage Verification

Status: Ready for agent
Parent PRD or proposal: `docs/prd/026-m68k-tool-replacement-and-unsupported-closure.md`
Type: AFK
Blocked by: `docs/issues/026-003-delete-legacy-form-identity-and-fallback-paths.md`

## Scope

Run and document the final verification set for the generated coverage rewrite.

Final coverage verification must use:

```powershell
uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical
```

## Out of scope

- New feature implementation found during verification.
- Changing oracle behavior.

## Files likely touched

- `docs/issues/`
- `src/tests/generated/`
- `tests/`

## Acceptance criteria

- [ ] Strict form coverage test passes.
- [ ] `uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical` passes.
- [ ] Stale unsupported inventory test passes.
- [ ] Assembler corpus regenerates cleanly.
- [ ] Oracle corpus checks run for CPU tiers where oracle support exists.
- [ ] Decode/disasm parity report has no unexplained required mismatches.
- [ ] Decode -> render -> assemble parity passes for every renderable decoded case where round-trip rendering is expected.
- [ ] C backend assembler/disassembler/simulator tests pass for affected areas.
- [ ] Any residual unsupported state is represented in canonical unsupported inventory.

## Required tests

- [ ] Run the repository's relevant Python tests.
- [ ] Run the relevant C backend tests.
- [ ] Run renderer round-trip parity tests for declared renderable forms.
- [ ] Run vasm oracle corpus checks where locally available.

## Cleanup / deletion

- Record any unavailable oracle tools as verification limitations, not as passing checks.

## Notes for agents

Do not mark the rewrite complete if strict coverage is passing only because required forms were downgraded without structured reasons.
