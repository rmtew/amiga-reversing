# 019-001: Coverage Current-Output Hooks

Status: active

## Proposal Context

- Source proposal: `docs/proposals/019-platform-executable-kb-parser-consumption.md`
- Depends on Proposal 018 being complete as the executable-format KB authority.
- Purpose: extend platform executable coverage so current Amiga and Atari parser
  outputs can be included like the current Mac C backend output.

## Scope

Add coverage command options:

- `--current-amiga-hunk`
- `--current-atari-prg`

These options must call real parser/import summary code. Synthetic fixture bytes
are acceptable only if they drive the same parser code path that production
input uses.

## Out of Scope

- Do not add Amiga/Atari fact refs in this issue unless a minimal ref is needed
  to prove the hook shape.
- Do not reopen Proposal 018.
- Do not handcraft parser output dictionaries as the implementation.

## Files Likely Touched

- `amiga_reversing/tools/platform_executable_formats.py`
- relevant Amiga/Atari parser helper modules
- `tests/test_platform_executable_formats.py`
- parser-specific tests if helpers are introduced

## Acceptance Criteria

- [ ] `coverage --current-amiga-hunk` runs parser/import code and returns JSON.
- [ ] `coverage --current-atari-prg` runs parser/import code and returns JSON.
- [ ] Both options can be combined with `--current-macos-c-backend`.
- [ ] Empty coverage still fails unless `--allow-empty` is explicit.
- [ ] Tests prove the hooks are not handcrafted payload shortcuts.

## Required Tests

Run:

```text
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-amiga-hunk --current-atari-prg --current-macos-c-backend
uv run python -m pytest tests\test_platform_executable_formats.py -q
git diff --check
```

Add parser-specific tests if helper code is touched.

## Cleanup / Deletion

Delete this issue after completion only after Proposal 019 records the durable
hook behavior.

## Notes for Agents

This is implementation work. If the parser cannot emit useful fact refs yet, the
hook may initially report that platform output as parser-output with zero facts,
but the later platform issues must make it report real refs. Do not complete
019-004 until all three platforms emit meaningful refs.

