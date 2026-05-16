Status: Open
Parent PRD or proposal: `docs/proposals/005-m68k-generated-coverage.md`

Scope:
Emit and consume direct lookup tables keyed by canonical form id, reducing
runtime scans and fallback matching.

Out of scope:
Changing instruction semantics or adding unsupported families.

Files likely touched:
Canonical model generator, assembler/disassembler/simulator generators,
`src/m68k_assembler.c`, `src/m68k_disassembler.c`, `src/m68k_simulator.c`, and
C tests.

Acceptance criteria:
- [ ] Generated data includes canonical id to assembler row lookup.
- [ ] Generated data includes canonical id to disassembler/render row lookup where applicable.
- [ ] Generated data includes canonical id to simulator metadata/status lookup.
- [ ] Simulator metadata lookup no longer linearly scans `g_m68k_sim_form_lookup`.
- [ ] Any remaining assembler candidate scan is justified as a generated candidate range, not whole-table fallback.
- [ ] Old scan/fallback code made redundant by generated lookups is deleted.

Required tests:
- [ ] C test for canonical id to asm/disasm/sim lookup.
- [ ] Regenerate affected assembler/disassembler/simulator artifacts with the relevant generator commands from Proposal 005.
- [ ] Run relevant generator/codegen tests.
- [ ] `cmd /c src\precommit.bat`
- [ ] `uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical`

Cleanup / deletion:
Delete this issue after direct lookups are generated and old scan paths are
removed or explicitly justified in the proposal.

Blocked by:
- `027-004-extract-canonical-model-generator.md`
- `027-005-split-generated-form-model-storage.md`

Notes for agents:
Blocked by `027-004`; easier after `027-005`.

Running precommit may update `src\benchmark.json`; keep it if it reflects the
current run.
