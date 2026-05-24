# 019-001: Amiga HUNK Current KB Fact Output

Status: active

## Proposal Context

- Source proposal: `docs/proposals/019-platform-executable-kb-parser-consumption.md`
- Proposal 018 is complete as the executable-format KB authority.
- Purpose: make current Amiga HUNK parser/import output emit executable-format
  KB fact refs and make coverage validate that real parser output.

## What to Build

Implement a real current-output path:

```text
platform_executable_formats coverage --current-amiga-hunk
```

The command must execute Amiga HUNK parser/import code, not return a handcrafted
payload. Synthetic fixture bytes are allowed only if they are parsed by the
same HUNK parser/import path as normal input.

The emitted output must include:

- `kb_record_id: amiga.hunk.load_file.basic_backfill`;
- at least one accepted/parser-asserted fact ref from the Amiga HUNK record;
- CODE/DATA/BSS section role refs where the parser sees those sections;
- BSS size-only ref where the fixture covers BSS;
- at least one candidate/deferred/unsupported limit ref for parser breadth that
  is not accepted, such as runtime entry, overlay/loader variants, or parser
  migration limits.

## Out of Scope

- Do not implement full relocation, overlay, or symbol semantics.
- Do not change Amiga rendered source unless parser summary tests prove it is
  necessary.
- Do not reopen Proposal 018 or promote candidate/deferred facts.
- Do not satisfy this issue with a zero-fact hook.

## Files Likely Touched

- `src/platform_amiga_hunk.c`
- generated platform executable fact constants if needed
- `amiga_reversing/tools/platform_executable_formats.py`
- `tests/test_platform_executable_formats.py`
- `tests/test_c_backend.py` or the closest existing HUNK parser tests

## Acceptance Criteria

- [ ] `coverage --current-amiga-hunk` runs real HUNK parser/import code.
- [ ] The emitted parser output validates against
  `knowledge/platform_executable_formats.json` with `invalid: 0`.
- [ ] Coverage summary for Amiga includes accepted/parser-asserted fact refs.
- [ ] Coverage summary also includes non-accepted candidate/deferred/unsupported
  limits where the parser has known unimplemented breadth.
- [ ] Tests fail if `--current-amiga-hunk` emits zero fact refs.
- [ ] Tests fail if candidate/deferred/unsupported HUNK facts are emitted as
  accepted parser output.

## Required Tests

Run:

```text
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-amiga-hunk
uv run python -m pytest tests\test_platform_executable_formats.py tests\test_c_backend.py -q
git diff --check
```

If C parser code changes, run the C build/precommit command used by the repo.

## Cleanup / Deletion

Delete this issue after completion only after Proposal 019 records the Amiga
parser consumption result.

## Notes for Agents

The valuable result is maintainable parser output that explains its authority.
Keep the implementation narrow, but make it real.

