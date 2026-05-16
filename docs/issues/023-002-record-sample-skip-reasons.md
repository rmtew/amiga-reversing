# Record Sample Skip Reasons

Status: Ready for agent
Parent PRD or proposal: `docs/prd/023-m68k-diagnostic-coverage-manifest.md`
Type: AFK
Blocked by: `docs/issues/023-001-build-diagnostic-form-inventory.md`

## Scope

Replace silent assembler corpus skips with explicit coverage entries that record why a form was not sampled.

## Out of scope

- Generating final sample plans.
- Implementing unsupported instruction families.

## Files likely touched

- `src/scripts/generate_c99_assembler_corpus.py`
- `src/scripts/`
- `tests/`

## Acceptance criteria

- [ ] Empty sample option paths record a manifest status instead of only continuing.
- [ ] Missing sample strategy is distinct from intentionally unsupported and implemented unsupported.
- [ ] Report output can list forms skipped for missing sample strategy.

## Required tests

- [ ] Test a form with missing options produces `missing_sample_strategy`.
- [ ] Test intentional unsupported state is not reported as missing sample strategy.

## Cleanup / deletion

- Fold this status recording into generated sample-plan coverage in PRD 025.

## Notes for agents

Do not add mnemonic-specific sample workarounds here.
