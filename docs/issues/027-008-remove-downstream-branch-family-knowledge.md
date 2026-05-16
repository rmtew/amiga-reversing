Status: Open
Parent PRD or proposal: `docs/proposals/005-m68k-generated-coverage.md`

Scope:
Replace the remaining downstream branch-family switch in source recovery with
generated form/mnemonic family or simulator flow metadata.

Out of scope:
Broad source recovery refactors.

Files likely touched:
Generated metadata, `src/platform_file_core.c`, related headers, and C tests.

Acceptance criteria:
- [ ] `platform_file_core.c` no longer hardcodes branch mnemonic ids.
- [ ] Byte-sized branch target recovery uses generated metadata.
- [ ] Tests cover a byte branch target recovery path through generated metadata.
- [ ] Proposal deletion checklist is updated if another downstream family switch is discovered.
- [ ] Replacement metadata is generated from canonical form/family or simulator flow data, not a new downstream switch.

Required tests:
- [ ] C unit or integration test for byte branch target recovery.
- [ ] Regenerate generated metadata with the relevant generator command from Proposal 005 if the replacement uses new generated family/flow data.
- [ ] Run relevant generator/codegen test if generated metadata changes.
- [ ] `cmd /c src\precommit.bat`
- [ ] `uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical`

Cleanup / deletion:
Delete this issue after downstream branch-family knowledge is removed and any
new durable finding is promoted to the proposal.

Blocked by:
- `027-004-extract-canonical-model-generator.md`
- `027-006-direct-canonical-lookup-tables.md`

Notes for agents:
Blocked by `027-004` or `027-006`, depending on where generated family metadata
lands.

Running precommit may update `src\benchmark.json`; keep it if it reflects the
current run.
