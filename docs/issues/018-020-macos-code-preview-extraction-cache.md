# 018-020: Mac OS CODE Preview Extraction Cache

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS CODE preview payload performance and repeated
  extraction control
- Blocked by: `018-017`
- Work order: safe after `018-019` or in parallel only if it avoids changing
  preview row semantics.
- Current proposal state: preview generation can call CODE resource extraction
  separately for each previewable resource while building the Mac project
  payload.
- Desired proposal state after this issue: Mac CODE preview payload construction
  avoids unnecessary repeated extraction, with bounded cache/profile evidence
  and unchanged preview semantics.

## Knowledge Delta

- Adds: performance/caching requirements for Mac CODE resource preview
  extraction.
- Changes: payload build should reuse extracted CODE payload bytes per resource.
- Replaces: repeated extraction as an implicit side effect of preview generation.
- Deletes: no preview data or evidence.
- Leaves out of scope: changing decoded/fallback row semantics, relocation
  interpretation, and web UI redesign.

## Default Behavior

- Cache scope must be local to one payload build unless a broader cache is
  explicitly justified and invalidated.
- Cache keys must include source image/HFS path/resource id.
- Output payloads must be byte-for-byte or structurally equivalent except for
  optional profile/debug evidence.
- Candidate/deferred fact state must not change.

## Evidence Standard

- Tests must prove repeated resource preview generation does not repeatedly call
  extraction for the same CODE resource in one payload build.
- Tests must prove cache isolation across different HFS paths or resource ids.
- Any profile/debug output must be deterministic and not pollute user-facing
  facts.

## Implementation Slice

- Trace current preview extraction call sites.
- Add a small local extraction cache for Mac project payload generation.
- Add tests with an instrumented extractor.
- Keep web/artifact rendering unchanged unless cache profile fields are exposed.
- Update docs only if user-visible behavior or profiling output changes.

## Research Completion Standard

Record trace blocks for:

- extraction call path;
- cache key shape;
- cache lifetime;
- tests proving hit/isolation behavior;
- unchanged candidate/deferred semantics.

## Research Notes

Trace blocks:

```text
Extraction call path:
  build_macos_project_payload -> _binary_container_view ->
  _code_resource_details -> _preview_windows ->
  _extract_macos_code_resource_payload.

Cache key shape:
  (source_image, hfs_path, resource_id). The source image is threaded from the
  Mac project origin into the binary container view; HFS path and CODE id come
  from the current preview request.

Cache lifetime:
  A plain dict is allocated inside one _binary_container_view call and passed
  through preview generation. It is discarded when that payload build returns.

Semantics:
  The helper returns the exact bytes from the existing C extractor on a miss and
  does not add payload/debug fields. Candidate/deferred parser fact state and
  decoded/fallback preview row semantics are unchanged.
```

## Completion Evidence

```text
uv run python -m pytest tests\test_macos_project_payload.py -q
3 passed
uv run ruff check amiga_reversing\disasm\macos_project_payload.py tests\test_macos_project_payload.py
All checks passed!
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.validate_018_issues
```

## Research Coverage

- [x] Current extraction call path traced.
- [x] Cache key selected.
- [x] Cache lifetime selected.
- [x] Test strategy selected.
- [x] User-visible output impact checked.
- [x] 018 wording checked before implementation.

## Research Review

- [x] Second pass checked cache does not change preview semantics.
- [x] Cache isolation across resource ids checked.
- [x] Cache isolation across HFS paths checked if applicable.
- [x] Candidate/deferred facts remain unchanged.
- [x] Relevant docs updated if output changes.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Local extraction cache added or a documented no-op decision recorded.
- [x] Repeated extraction test added.
- [x] Cache isolation test added.
- [x] Candidate/deferred facts are not changed.
- [x] Relevant payload tests pass.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.
