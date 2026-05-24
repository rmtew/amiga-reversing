# 019-002: Amiga HUNK Parser Fact Refs

Status: active

## Proposal Context

- Source proposal: `docs/proposals/019-platform-executable-kb-parser-consumption.md`
- Depends on `docs/issues/019-001-coverage-current-output-hooks.md`
- Purpose: make Amiga HUNK parser/import output consume and emit the Amiga HUNK
  executable-format KB record from Proposal 018.

## Scope

Emit fact refs for the current accepted/parser-asserted Amiga slice:

- `amiga.hunk.load_file.basic_backfill`;
- HUNK header identity;
- CODE/DATA/BSS section roles;
- object/library container identity where the current parser can distinguish it;
- size-only BSS;
- candidate/deferred/unsupported refs for known unsupported breadth where the
  parser currently reports or encounters it.

## Out of Scope

- Do not implement full relocation/overlay/symbol semantics.
- Do not change rendered Amiga source unless a test proves the parser summary
  change requires it.
- Do not promote candidate/deferred facts.

## Files Likely Touched

- Amiga HUNK parser/import summary modules
- `amiga_reversing/tools/platform_executable_formats.py` if hook wiring needs
  refinement
- `tests/test_platform_executable_formats.py`
- Amiga parser tests

## Acceptance Criteria

- [ ] Current Amiga HUNK coverage emits at least one accepted/parser-asserted KB
  fact ref from the Amiga record.
- [ ] CODE/DATA/BSS roles are represented with KB fact ids where parsed.
- [ ] Deferred/unsupported breadth is not reported as accepted.
- [ ] `coverage --current-amiga-hunk` reports no invalid fact refs.
- [ ] Tests exercise parser-produced output, not only handcrafted payloads.

## Required Tests

Run:

```text
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-amiga-hunk
uv run python -m pytest tests\test_platform_executable_formats.py -q
git diff --check
```

Run relevant Amiga HUNK parser tests discovered during implementation.

## Cleanup / Deletion

Delete this issue after completion only after Proposal 019 records the Amiga
parser consumption result.

## Notes for Agents

Small, real parser output beats broad redesign. The objective is KB-backed fact
emission on the current parser surface.

