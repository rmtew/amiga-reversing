Status: Open
Parent PRD or proposal: `docs/proposals/005-m68k-generated-coverage.md`

Scope:
Make canonical coverage consume real generated canonical form ids from the
current assembler and disassembler generated forms, then fail strict mode when
those ids disagree.

Out of scope:
Changing canonical id assignment, extracting the canonical model generator, or
changing simulator semantics.

Files likely touched:
`amiga_reversing/tools/m68k_coverage.py`, `tests/test_m68k_coverage.py`, and
possibly the generated-form loader helpers.

Acceptance criteria:
- [ ] Canonical inventory entries include assembler and disassembler canonical ids when present.
- [ ] `check --phase canonical` fails on a real generated asm/disasm canonical id mismatch.
- [ ] Synthetic-only canonical mismatch coverage is replaced or backed by loaded generated data.
- [ ] Successful canonical check prints canonical-oriented output, not only diagnostic output.
- [ ] Coverage compares generated artifacts or independently loaded generated tables; it does not only recompute ids through the same helper path that produced them.

Required tests:
- [ ] Focused pytest coverage for real canonical id parity.
- [ ] `uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical`
- [ ] `uv run python -m pytest tests\test_m68k_coverage.py -q`
- [ ] `cmd /c src\precommit.bat`

Cleanup / deletion:
Delete this issue after the proposal records any durable findings and the checks
above pass.

Blocked by:
None - can start immediately.

Notes for agents:
The visible improvement is that canonical coverage becomes a real gate, not a
report that only proves synthetic mismatch handling.

Running precommit may update `src\benchmark.json`; keep it if it reflects the
current run.
