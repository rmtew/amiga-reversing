Status: Open
Parent PRD or proposal: `docs/proposals/005-m68k-generated-coverage.md`

Scope:
Audit and replace remaining downstream M68K flow/family classifications that use
mnemonic id ranges or local mnemonic lists instead of generated metadata.

Out of scope:
Exact mnemonic checks that are truly domain-specific and cannot be expressed as
flow/family metadata. These must be documented in the proposal or issue before
this issue is closed.

Files likely touched:
`src/m68k_decode_ir.c`, `src/m68k_symbolic_parse.c`,
`src/platform_amiga_bootloader_analysis.c`,
`src/m68k_analysis_render_lookup.c`, `src/m68k_render_ir.c`, and focused tests.

Acceptance criteria:
- [ ] Remaining Bcc/DBcc/BRA/BSR/JMP/JSR/RTS/RTE/RTR flow-family checks are audited.
- [ ] Range/list checks that classify branch, DBcc, call, jump, return, or fallthrough behavior use generated mnemonic family or simulator flow metadata.
- [ ] Exact mnemonic checks that remain have a documented reason and are not masquerading as family classification.
- [ ] Decode target classification still records branch/call/jump targets correctly.
- [ ] Bootloader analysis and render analysis behavior covered by changed paths still passes focused tests.
- [ ] Proposal 005 deletion checklist/state assessment updated with the actual final result.

Required tests:
- [ ] Focused C unit/integration tests for each changed classifier path.
- [ ] `src\build\m68k_c_unit_tests.exe`
- [ ] `uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical`
- [ ] `cmd /c src\precommit.bat`

Cleanup / deletion:
Delete this issue after all remaining flow/family classification findings are
removed or explicitly justified in Proposal 005.

Blocked by:
- None

Notes for agents:
Do not replace exact domain behavior blindly. Use generated simulator metadata
for flow classification and generated mnemonic metadata for family/render
classification. If a path needs exact instruction identity, document why.
