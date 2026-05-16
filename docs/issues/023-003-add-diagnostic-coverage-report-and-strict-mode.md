# Add Diagnostic Coverage Report And Strict Mode

Status: Ready for agent
Parent PRD or proposal: `docs/prd/023-m68k-diagnostic-coverage-manifest.md`
Type: AFK
Blocked by: `docs/issues/023-002-record-sample-skip-reasons.md`

## Scope

Add readable report mode and initial strict mode for the diagnostic manifest through the shared coverage command surface.

```powershell
uv run python -m amiga_reversing.tools.m68k_coverage report --phase diagnostic
uv run python -m amiga_reversing.tools.m68k_coverage check --phase diagnostic
```

## Out of scope

- CI enforcement unless existing test conventions make it trivial.
- Final canonical strict gate.

## Files likely touched

- `src/scripts/`
- `tests/`

## Acceptance criteria

- [ ] Report mode prints form counts, match counts, sample status counts, and unsupported counts.
- [ ] Strict mode fails when a generated form is unclassified.
- [ ] Strict mode fails on missing sample strategy unless the caller requests report-only behavior.
- [ ] The report and check commands can be generated without inspecting test internals.

## Required tests

- [ ] Test report mode succeeds with current classified data.
- [ ] Test strict mode fails on synthetic unclassified data.
- [ ] Test strict mode fails on synthetic missing sample strategy data.

## Cleanup / deletion

- Replace with canonical-model report mode and strict mode.

## Notes for agents

Keep output stable enough for tests, but do not overfit formatting if structured assertions are easier. Do not add a separate corpus-generator coverage flag or command.
