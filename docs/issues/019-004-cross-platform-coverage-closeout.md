# 019-004: Cross-Platform Coverage Closeout

Status: active

## Proposal Context

- Source proposal: `docs/proposals/019-platform-executable-kb-parser-consumption.md`
- Depends on:
  - `docs/issues/019-001-coverage-current-output-hooks.md`
  - `docs/issues/019-002-amiga-hunk-parser-fact-refs.md`
  - `docs/issues/019-003-atari-prg-parser-fact-refs.md`
- Purpose: make current-output coverage prove that Mac, Amiga, and Atari parser
  outputs all consume the executable-format KB without invalid accepted claims.

## Scope

Close the first Proposal 019 implementation loop:

```text
coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
```

The result should prove:

- all three current-output paths run;
- invalid accepted claims are zero;
- Amiga and Atari are no longer unreported platform records for their accepted
  first slices;
- candidate/deferred/unsupported facts remain non-accepted.

## Out of Scope

- Do not broaden parser semantics beyond the first KB consumption slices.
- Do not reopen Proposal 018.
- Do not generate target source/artifact churn.

## Files Likely Touched

- `docs/proposals/019-platform-executable-kb-parser-consumption.md`
- coverage tests
- small report/test cleanup if earlier slices left inconsistencies

## Acceptance Criteria

- [ ] Cross-platform current coverage command passes with `invalid: 0`.
- [ ] Mac, Amiga, and Atari current parser outputs are represented.
- [ ] No accepted parser output comes from candidate/deferred/unsupported facts.
- [ ] Proposal 019 records the implemented consumption state and remaining
  future work.
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

Run parser-specific tests touched by 019-002 and 019-003.

## Cleanup / Deletion

Delete this issue after completion only after Proposal 019 records the closeout
state.

## Notes for Agents

This is not a research closeout. It should verify the code paths built by the
previous issues and leave the repo with a stronger default executable-format
coverage gate.

