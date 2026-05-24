# 019-003: Cross-Platform Current Coverage Gate

Status: active

## Proposal Context

- Source proposal: `docs/proposals/019-platform-executable-kb-parser-consumption.md`
- Blocked by:
  - `docs/issues/019-001-amiga-hunk-current-kb-fact-output.md`
  - `docs/issues/019-002-atari-prg-current-kb-fact-output.md`
- Purpose: make the executable-format coverage gate prove current parser
  consumption for Mac, Amiga, and Atari together.

## What to Build

Make this command a real closeout gate:

```text
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
```

The combined report must show:

- Mac, Amiga, and Atari current parser outputs are present;
- `invalid: 0`;
- Amiga and Atari accepted first-slice records are no longer unreported;
- candidate/deferred/unsupported facts remain non-accepted;
- the command fails if either Amiga or Atari current output becomes empty.

## Out of Scope

- Do not broaden parser semantics beyond 019-001 and 019-002.
- Do not reopen Proposal 018.
- Do not create target source/artifact churn.

## Files Likely Touched

- `amiga_reversing/tools/platform_executable_formats.py`
- `tests/test_platform_executable_formats.py`
- `docs/proposals/019-platform-executable-kb-parser-consumption.md`

## Acceptance Criteria

- [ ] Combined current-output coverage passes with `invalid: 0`.
- [ ] The report includes parser outputs for all three platforms.
- [ ] No accepted parser output comes from candidate/deferred/unsupported facts.
- [ ] Tests fail if Amiga or Atari parser-output fact refs disappear.
- [ ] Proposal 019 records the implemented cross-platform consumption state.
- [ ] Completed 019 issue files are deleted only after durable conclusions are
  promoted into Proposal 019.

## Required Tests

Run:

```text
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
uv run python -m pytest tests\test_platform_executable_formats.py -q
git diff --check
```

Run parser-specific tests touched by 019-001 and 019-002.

## Cleanup / Deletion

Delete this issue after completion only after Proposal 019 records the closeout
state.

## Notes for Agents

This is not a report about what remains blocked. It is the proof that current
parser output is now mechanically checked against the KB for all three
platforms.

