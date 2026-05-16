Status: Open
Parent PRD or proposal: `docs/proposals/005-m68k-generated-coverage.md`

Scope:
Make simulator generated metadata distinguish available semantics from missing
or intentionally unsupported semantics, and make coverage consume that status.

Out of scope:
Implementing missing instruction semantics.

Files likely touched:
`src/scripts/generate_c99_simulator_subset.py`, `src/generated/m68k_simulator_tables.h`,
`src/m68k_simulator.c`, `src/m68k_simulator.h`,
`amiga_reversing/tools/m68k_coverage.py`, and simulator/coverage tests.

Acceptance criteria:
- [ ] Simulator generator emits per-canonical-form semantic status.
- [ ] Not every emitted simulator row is blindly marked `M68K_SIM_SEMANTICS_AVAILABLE`.
- [ ] Runtime lookup reports generated-semantics-missing from generated status.
- [ ] Canonical coverage summary reports simulator semantic counts from generated data.
- [ ] Unsupported inventory uses simulator semantic status as a real blocker.
- [ ] Simulator status names match Proposal 005 vocabulary: available, generated_semantics_missing, intentionally_unsupported.

Required tests:
- [ ] C unit test for available and missing semantic lookup paths.
- [ ] Pytest coverage for semantic status summary.
- [ ] Regenerate simulator generated artifacts with `uv run python src\scripts\generate_c99_simulator_subset.py`.
- [ ] Run relevant simulator generator/codegen tests.
- [ ] Run simulator oracle tests/integration tests when semantic status affects oracle-backed forms.
- [ ] `cmd /c src\precommit.bat`
- [ ] `uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical`

Cleanup / deletion:
Delete this issue after semantic status and coverage agree.

Blocked by:
None - can start immediately.

Notes for agents:
The visible improvement is that executor/simulator coverage stops conflating
"metadata row exists" with "semantics are trustworthy."

Running precommit may update `src\benchmark.json`; keep it if it reflects the
current run.
