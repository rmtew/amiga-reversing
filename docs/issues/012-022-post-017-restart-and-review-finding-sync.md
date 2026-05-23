# 012-022: Post-017 Restart and Review Finding Sync

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/012-classic-mac-os-m68k-platform.md`
- Current proposal state: 017 has been restarted and completed through the
  Pandora baseline follow-up; the completed 017 issue files were removed after
  their validation commits. This file is the active 012 issue trail restart.
- Current blocker state: 012 remains open/blocked for full closeout on accepted
  Mac executable byte-entry and relocation/fixup knowledge. 018-026 and 018-027
  now explicitly record those blockers as deferred rather than uncommitted
  work.
- Desired state after this issue: restart 012 work with a current issue trail,
  verify known review findings, and keep the 012 sync commit focused on review
  finding status rather than changing 018 executable-format behavior.

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

## Completion Audit

Requirements and evidence:

- 012 issue trail restarted: this issue remains under `docs/issues/012-*` and
  records the post-017 state instead of relying on the consolidated proposal
  alone.
- Known review findings verified: each finding above is tied to a current code
  path and regression test.
- 018 scope not mixed into this issue: byte-entry and relocation/fixup behavior
  remain governed by the completed 018 follow-up records; this issue changes no
  parser, payload, web, or KB behavior.
- Proposal state synchronized: Proposal 012 already records the review cleanup
  and the later 018 blocker matrix; this issue now references the current
  deferred blocker state instead of stale uncommitted 018 work.

## Completion Evidence

- `pytest tests\test_macos_resource_model.py tests\test_macos_source_structure.py tests\test_mac_fork_roles.py -q`
  passed: 15 tests.
- `ruff check` on the related Mac parser/classifier/test files passed.
- Current audit rerun:
  `uv run python -m pytest tests\test_macos_resource_model.py tests\test_macos_source_structure.py tests\test_mac_fork_roles.py -q`
  passed: 15 tests.
- Current lint rerun:
  `uv run ruff check amiga_reversing\disasm\macos_resource_model.py amiga_reversing\disasm\macos_source_structure.py amiga_reversing\disasm\macos_fork_roles.py tests\test_macos_resource_model.py tests\test_macos_source_structure.py tests\test_mac_fork_roles.py`
  passed: all checks.
- Available issue validator rerun:
  `uv run python -m amiga_reversing.tools.validate_017_issues`
  passed.
- Current repository check: `git status --short` was clean before this docs-only
  sync edit.

## Next Step

Do not reopen these three findings. Continue 012 only where it is not blocked
by 018; otherwise let later executable-format evidence resolve the byte-entry
and relocation/fixup blockers before final 012 closeout.
