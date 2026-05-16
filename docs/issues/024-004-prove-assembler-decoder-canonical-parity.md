# Prove Assembler Decoder Canonical Parity

Status: Ready for agent
Parent PRD or proposal: `docs/prd/024-m68k-canonical-form-model.md`
Type: AFK
Blocked by: `docs/issues/024-002-migrate-assembler-view-to-canonical-forms.md`, `docs/issues/024-003-migrate-disassembler-view-to-canonical-forms.md`

## Scope

Add parity tests showing that assembler output decodes back to the same canonical form id for currently sampleable forms.

## Out of scope

- Final generated sample-plan coverage.
- Unsupported-family implementation.

## Files likely touched

- `tests/`
- `src/test_*.c`
- `src/scripts/`

## Acceptance criteria

- [ ] Each available generated sample case records the assembler canonical form id.
- [ ] Decoding the assembled bytes recovers the same canonical form id.
- [ ] Mismatches fail with enough detail to identify the form and source case.

## Required tests

- [ ] Run parity over current sampleable generated corpus.
- [ ] Add a focused regression fixture for at least one alias or conditional-family form.

## Cleanup / deletion

- Replace any temporary diagnostic parity harness with canonical strict coverage in PRD 025.

## Notes for agents

Treat parity mismatches as rewrite closure failures, not deferred cleanup.
