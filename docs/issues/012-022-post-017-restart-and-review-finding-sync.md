# 012-022: Post-017 Restart and Review Finding Sync

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/012-classic-mac-os-m68k-platform.md`
- Current proposal state: 017 is paused after a clean Pandora baseline. 012 has
  no active `docs/issues/012-*` issue files because the older set was previously
  consolidated into the proposal.
- Current blocker state: 012 remains open/blocked on accepted Mac executable
  byte-entry and relocation/fixup knowledge. Existing uncommitted 018-026 work
  already updates the proposal with the current byte-entry blocker.
- Desired state after this issue: restart 012 work with a current issue trail,
  verify known review findings, and avoid mixing the 018-026 proposal edits into
  this commit.

## Review Findings Checked

- Rez/resource ID resolution must not turn unknown symbolic IDs into numeric
  `0`.
- MPW source structure parsing must treat MPW continuation glyphs U+00B6 and
  U+2202 like backslash continuations.
- Mac fork role classification should treat `OBJ `, `XCOF`, and `stub` data
  forks as object/library-like payloads instead of unknown.

## Result

All three findings were already addressed in the current codebase:

- `amiga_reversing/disasm/macos_resource_model.py` resolves unknown names to
  `None`, and `tests/test_macos_resource_model.py` covers unresolved symbolic
  and expression IDs.
- `amiga_reversing/disasm/macos_source_structure.py` has
  `_CONTINUATION_SUFFIXES = ("\\", "\u00b6", "\u2202")`, and
  `tests/test_macos_source_structure.py` covers both MPW glyphs.
- `amiga_reversing/disasm/macos_fork_roles.py` classifies `OBJ `, `XCOF`, and
  `stub` as `object_payload`, and `tests/test_mac_fork_roles.py` covers all
  three.

## Verification

- `pytest tests\test_macos_resource_model.py tests\test_macos_source_structure.py tests\test_mac_fork_roles.py -q`
  passed: 15 tests.
- `ruff check` on the related Mac parser/classifier/test files passed.

## Next Step

Do not reopen these three findings. Continue 012 only where it is not blocked
by 018; otherwise let 018-026 and later executable-format issues resolve the
byte-entry/relocation blockers before final 012 closeout.
