# 019-003: Atari PRG Parser Fact Refs

Status: active

## Proposal Context

- Source proposal: `docs/proposals/019-platform-executable-kb-parser-consumption.md`
- Depends on `docs/issues/019-001-coverage-current-output-hooks.md`
- Purpose: make Atari ST PRG parser/import output consume and emit the Atari
  PRG executable-format KB record from Proposal 018.

## Scope

Emit fact refs for the current accepted/parser-asserted Atari slice:

- `atari_st.prg.gemdos_basic_backfill`;
- 0x601A PRG magic;
- PRG header and TEXT/DATA/BSS sequence;
- TEXT/DATA/BSS region shape;
- TEXT+DATA loaded-image relocation target space;
- candidate/deferred/unsupported refs for runtime/basepage/symbol details where
  the parser currently reports or encounters them.

## Out of Scope

- Do not implement full GEMDOS runtime/basepage semantics.
- Do not implement new symbol-table behavior unless it is already parser-owned
  and only needs fact refs.
- Do not promote candidate/deferred facts.

## Files Likely Touched

- Atari PRG parser/import summary modules
- `amiga_reversing/tools/platform_executable_formats.py` if hook wiring needs
  refinement
- `tests/test_platform_executable_formats.py`
- Atari parser tests

## Acceptance Criteria

- [ ] Current Atari PRG coverage emits at least one accepted/parser-asserted KB
  fact ref from the Atari record.
- [ ] TEXT/DATA/BSS region shape is represented with KB fact ids where parsed.
- [ ] Deferred/unsupported breadth is not reported as accepted.
- [ ] `coverage --current-atari-prg` reports no invalid fact refs.
- [ ] Tests exercise parser-produced output, not only handcrafted payloads.

## Required Tests

Run:

```text
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-atari-prg
uv run python -m pytest tests\test_platform_executable_formats.py -q
git diff --check
```

Run relevant Atari PRG parser tests discovered during implementation.

## Cleanup / Deletion

Delete this issue after completion only after Proposal 019 records the Atari
parser consumption result.

## Notes for Agents

Do not let “full Atari semantics” block this. The accepted 018 slice is narrow;
emit refs for that slice and leave deeper facts candidate/deferred.

