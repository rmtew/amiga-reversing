Status: Open
Parent PRD or proposal: `docs/proposals/005-m68k-generated-coverage.md`

Scope:
Move special operand sample knowledge out of the corpus generator and into
generated canonical sample-plan data.

Out of scope:
Expanding unsupported families solely for breadth.

Files likely touched:
Canonical model/sample-plan generator, `src/scripts/generate_c99_assembler_corpus.py`,
generated sample-plan artifacts, and coverage tests.

Acceptance criteria:
- [ ] Operand sample registry is generated from parser/schema/canonical model data.
- [ ] Per-form sample plans are generated artifacts consumed by the corpus generator.
- [ ] Corpus generator expands sample plans instead of constructing register-pair, cache-selector, bitfield-EA, and absolute-form samples locally.
- [ ] Missing sample strategy remains a strict coverage failure.
- [ ] EA family coverage report still shows required, covered, and missing families.
- [ ] Parser/schema/canonical-model data owns any newly needed M68K operand facts; corpus code does not add replacement special cases.

Required tests:
- [ ] Pytest coverage proving corpus reads generated sample plans.
- [ ] Regenerate assembler corpus artifacts with `uv run python src\scripts\generate_c99_assembler_corpus.py`.
- [ ] Run assembler corpus unit tests and integration tests.
- [ ] Run oracle/vasm corpus checks for any form whose oracle status or emitted source changes.
- [ ] `uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical`
- [ ] `uv run python -m pytest tests\test_m68k_coverage.py -q`
- [ ] `cmd /c src\precommit.bat`

Cleanup / deletion:
Delete this issue after corpus-local sample knowledge is removed or reduced to
plan expansion only.

Blocked by:
- `027-004-extract-canonical-model-generator.md`

Notes for agents:
Blocked by `027-004`.

Running precommit may update `src\benchmark.json`; keep it if it reflects the
current run.
