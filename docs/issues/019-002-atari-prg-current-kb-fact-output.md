# 019-002: Atari PRG Current KB Fact Output

Status: active

## Proposal Context

- Source proposal: `docs/proposals/019-platform-executable-kb-parser-consumption.md`
- Proposal 018 is complete as the executable-format KB authority.
- Purpose: make current Atari ST PRG parser/import output emit
  executable-format KB fact refs and make coverage validate that real parser
  output.

## What to Build

Implement a real current-output path:

```text
platform_executable_formats coverage --current-atari-prg
```

The command must execute Atari PRG parser/import code, not return a handcrafted
payload. Synthetic fixture bytes are allowed only if they are parsed by the
same Atari PRG parser/import path as normal input.

The emitted output must include:

- `kb_record_id: atari_st.prg.gemdos_basic_backfill`;
- at least one accepted/parser-asserted fact ref from the Atari PRG record;
- 0x601A magic/header refs;
- TEXT/DATA/BSS region shape refs where parsed;
- TEXT+DATA loaded-image relocation target ref where the current parser exposes
  that model;
- at least one candidate/deferred/unsupported limit ref for parser breadth that
  is not accepted, such as runtime/basepage, symbol details, relocation
  terminator variants, or parser migration limits.

## Out of Scope

- Do not implement full GEMDOS runtime/basepage semantics.
- Do not implement new symbol-table behavior unless the current parser already
  owns it and only needs fact refs.
- Do not reopen Proposal 018 or promote candidate/deferred facts.
- Do not satisfy this issue with a zero-fact hook.

## Files Likely Touched

- `src/platform_atari_st.c`
- `src/platform_file_atari_st.c`
- generated Atari PRG runtime helpers if needed
- `amiga_reversing/tools/platform_executable_formats.py`
- `tests/test_platform_executable_formats.py`
- existing Atari parser/import tests discovered during implementation

## Acceptance Criteria

- [ ] `coverage --current-atari-prg` runs real Atari PRG parser/import code.
- [ ] The emitted parser output validates against
  `knowledge/platform_executable_formats.json` with `invalid: 0`.
- [ ] Coverage summary for Atari includes accepted/parser-asserted fact refs.
- [ ] Coverage summary also includes non-accepted candidate/deferred/unsupported
  limits where the parser has known unimplemented breadth.
- [ ] Tests fail if `--current-atari-prg` emits zero fact refs.
- [ ] Tests fail if candidate/deferred/unsupported Atari facts are emitted as
  accepted parser output.

## Required Tests

Run:

```text
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-atari-prg
uv run python -m pytest tests\test_platform_executable_formats.py -q
git diff --check
```

Run the relevant Atari parser/import tests discovered during implementation. If
C parser code changes, run the C build/precommit command used by the repo.

## Cleanup / Deletion

Delete this issue after completion only after Proposal 019 records the Atari
parser consumption result.

## Notes for Agents

The accepted 018 Atari slice is narrow. Emit refs for that slice and leave
deeper runtime/symbol/relocation details candidate/deferred.

