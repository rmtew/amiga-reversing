Status: Open
Parent PRD or proposal: `docs/proposals/005-m68k-generated-coverage.md`

Scope:
Run the final Proposal 005 verification pass, close remaining deletion checklist
items, and update the proposal with the actual final state.

Out of scope:
Starting new unsupported-family implementation work.

Files likely touched:
`docs/proposals/005-m68k-generated-coverage.md`, coverage reports, generated
artifacts if drift is found, and tests only as needed for final closure.

Acceptance criteria:
- [ ] Proposal 005 follow-up findings are resolved, updated, or explicitly deferred with reasons.
- [ ] Deletion checklist items are removed from code or recorded as still-open issue references.
- [ ] Strict canonical coverage passes.
- [ ] Assembler/disassembler/simulator generated artifacts are current.
- [ ] Issue files for completed slices are deleted after durable reasoning is promoted.
- [ ] Any oracle check that could not run is documented in Proposal 005 with the skipped command, reason, and accepted deferral.

Required tests:
- [ ] `uv run python -m amiga_reversing.tools.m68k_coverage report --phase canonical`
- [ ] `uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical`
- [ ] `uv run python -m pytest tests\test_m68k_coverage.py -q`
- [ ] Regenerate any stale generated artifacts with the relevant generator commands from Proposal 005 before final checks.
- [ ] Run corpus/oracle checks for any assembler, disassembler, simulator, sample-plan, or oracle-facing change included in the final pass.
- [ ] `cmd /c src\precommit.bat`

Cleanup / deletion:
Delete this issue last, after all Proposal 005 follow-up issue files are either
completed and deleted or deliberately superseded.

Blocked by:
- `027-010-remove-remaining-downstream-flow-family-knowledge.md`

Notes for agents:
Blocked by the remaining Proposal 005 implementation slice, currently
`027-010`.

Running precommit may update `src\benchmark.json`; keep it if it reflects the
current run.
