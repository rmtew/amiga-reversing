Status: Open
Parent PRD or proposal: `docs/proposals/005-m68k-generated-coverage.md`

Scope:
Replace placeholder unsupported stale checks with computed blockers for current
generated data.

Out of scope:
Implementing MOVE16, FSAVE/FRESTORE, PMMU, or generic coprocessor support.

Files likely touched:
`amiga_reversing/tools/m68k_coverage.py`, `tests/test_m68k_coverage.py`, and
generated coverage/sample-plan readers.

Acceptance criteria:
- [ ] Unsupported entries compute stale status from actual blockers.
- [ ] Stale checks cover sample plan, decode/render metadata, generated semantics, and oracle support.
- [ ] Strict coverage fails when an unsupported entry has no remaining blocker.
- [ ] Unsupported report output names the blocker that keeps each family unsupported.

Required tests:
- [ ] Test that a resolved synthetic unsupported family fails as stale.
- [ ] Test that current unsupported families remain non-stale for concrete blockers.
- [ ] If oracle blocker state is read, add an oracle-unavailable/covered fixture test.
- [ ] `uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical`
- [ ] `uv run python -m pytest tests\test_m68k_coverage.py -q`
- [ ] `cmd /c src\precommit.bat`

Cleanup / deletion:
Delete this issue after blocker logic is real and durable reasoning is promoted
to the proposal.

Blocked by:
None - can start immediately.

Notes for agents:
Real canonical ids and simulator semantic status counts are now available from
completed issues 027-001 and 027-003.

Running precommit may update `src\benchmark.json`; keep it if it reflects the
current run.
