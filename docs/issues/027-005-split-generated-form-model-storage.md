Status: Open
Parent PRD or proposal: `docs/proposals/005-m68k-generated-coverage.md`

Scope:
Split generated canonical form model declarations from storage so large arrays
are not defined as `static const` in a header.

Out of scope:
Changing canonical model semantics or ids.

Files likely touched:
Canonical model generator, `src/generated/m68k_form_model.h` or replacement
`src/generated/m68k_forms.h`, new `src/generated/m68k_forms.c`, build scripts,
and C includes.

Acceptance criteria:
- [ ] Header exposes types, constants, extern arrays, and lookup declarations.
- [ ] C file owns canonical form array storage and lookup tables.
- [ ] Runtime code compiles without duplicate static canonical model copies.
- [ ] Generated artifact names match the proposal or the proposal is updated with the chosen names.

Required tests:
- [ ] Regenerate generated artifacts with the relevant generator commands from Proposal 005.
- [ ] Confirm generated artifact diff contains the expected header/source split.
- [ ] `cmd /c src\precommit.bat`
- [ ] `uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical`

Cleanup / deletion:
Delete this issue after generated storage is split and obsolete static-header
definitions are gone.

Blocked by:
- `027-004-extract-canonical-model-generator.md`

Notes for agents:
Blocked by `027-004`.

Running precommit may update `src\benchmark.json`; keep it if it reflects the
current run.
