Status: Open
Parent PRD or proposal: `docs/proposals/005-m68k-generated-coverage.md`

Scope:
Move canonical form identity ownership out of the assembler subset generator
into a dedicated canonical model generator/module consumed by all M68K generated
tooling.

Out of scope:
Changing generated ids beyond what is unavoidable and documented, or broad
runtime refactors.

Files likely touched:
`src/scripts/generate_c99_assembler_subset.py`,
`src/scripts/generate_c99_disassembler_subset.py`,
`src/scripts/generate_c99_simulator_subset.py`,
`src/scripts/generate_c99_assembler_corpus.py`, new canonical-model generator
module, generated artifacts, and tests.

Acceptance criteria:
- [ ] Canonical form loading, identity keys, id assignment, row mapping, aliases, and families live outside assembler generation.
- [ ] Assembler, disassembler, simulator, corpus, and coverage consume the same canonical model module.
- [ ] Generated canonical ids remain stable or any unavoidable id change is explained in the proposal.
- [ ] No generator imports assembler-subset internals just to compute canonical ids.
- [ ] A snapshot/golden test fails on accidental canonical id reorder.
- [ ] Any public-ish C structs, generated corpus manifests, diagnostics, or tests carrying canonical ids are checked for fallout.
- [ ] Old assembler-owned canonical helper paths are deleted rather than kept as a compatibility shim.

Required tests:
- [ ] Generator unit or pytest coverage for canonical id uniqueness and stability.
- [ ] Regenerate affected artifacts with the relevant generator commands from Proposal 005.
- [ ] Run assembler, disassembler, and simulator generator/codegen tests.
- [ ] Run focused coverage pytest.
- [ ] `uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical`
- [ ] `cmd /c src\precommit.bat`

Cleanup / deletion:
Delete this issue after canonical ownership is extracted and durable migration
notes are promoted to the proposal.

Blocked by:
- `027-001-real-canonical-coverage-gate.md`

Notes for agents:
Blocked by `027-001`; real coverage should guard the extraction.

Running precommit may update `src\benchmark.json`; keep it if it reflects the
current run.
