# Enable Canonical Strict Coverage Checks

Status: Ready for agent
Parent PRD or proposal: `docs/prd/025-m68k-generated-sample-plans-and-strict-coverage.md`
Type: AFK
Blocked by: None

## Scope

Move strict coverage checks from the diagnostic manifest to canonical-model reporting after generated sample plans and canonical unsupported inventory exist.

Canonical report and check behavior must be exposed through:

```powershell
uv run python -m amiga_reversing.tools.m68k_coverage report --phase canonical
uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical
```

This issue creates the canonical strict check surface. The final rewrite gate runs after legacy fallback paths are deleted in PRD 026.

## Out of scope

- Final runtime deletion work owned by PRD 026.
- Final rewrite completion gating owned by PRD 026.
- Unsupported-family implementation.

## Files likely touched

- `src/scripts/`
- `tests/`
- `src/generated/`

## Acceptance criteria

- [ ] Strict coverage fails on unclassified canonical forms.
- [ ] Strict coverage fails on required forms with no sample plan and no unsupported reason.
- [ ] Strict coverage fails on stale unsupported reasons.
- [ ] Strict coverage fails on assembler/decoder canonical form identity mismatch.
- [ ] Report mode includes CPU, mnemonic, EA family, alias, oracle, executor semantic, and unsupported summaries where data exists.
- [ ] Canonical report and check behavior uses `amiga_reversing.tools.m68k_coverage`, not corpus-generator-specific flags.
- [ ] Diagnostic manifest code is deleted or folded into canonical reporting when equivalent coverage exists.
- [ ] Documentation makes clear that final strict gating happens after legacy fallback deletion and final verification.

## Required tests

- [ ] Test each strict failure mode with fixtures.
- [ ] Test report mode on current generated data.
- [ ] Run assembler corpus regeneration and affected parity tests.

## Cleanup / deletion

- Delete bootstrap diagnostic manifest paths that duplicate canonical reporting.

## Notes for agents

Do not leave two independent sources of coverage truth. Do not treat this issue as final completion while legacy fallback paths can still mask bad metadata.
