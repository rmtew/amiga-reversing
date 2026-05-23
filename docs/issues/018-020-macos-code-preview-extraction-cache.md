# 018-020: Mac OS CODE Preview Extraction Cache

Status: open

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

## Research Coverage

- [ ] Current extraction call path traced.
- [ ] Cache key selected.
- [ ] Cache lifetime selected.
- [ ] Test strategy selected.
- [ ] User-visible output impact checked.
- [ ] 018 wording checked before implementation.

## Research Review

- [ ] Second pass checked cache does not change preview semantics.
- [ ] Cache isolation across resource ids checked.
- [ ] Cache isolation across HFS paths checked if applicable.
- [ ] Candidate/deferred facts remain unchanged.
- [ ] Relevant docs updated if output changes.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Local extraction cache added or a documented no-op decision recorded.
- [ ] Repeated extraction test added.
- [ ] Cache isolation test added.
- [ ] Candidate/deferred facts are not changed.
- [ ] Relevant payload tests pass.
- [ ] `amiga_reversing.tools.validate_018_issues` passes.
- [ ] Post-commit review found no unresolved worthwhile findings.
