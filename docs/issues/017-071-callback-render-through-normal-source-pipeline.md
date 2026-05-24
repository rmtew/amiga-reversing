# 017-071: Callback Render Through Normal Source Pipeline

Status: complete
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: rendering accepted callback code classification.
- Current proposal state: `017-066` was superseded because render support is only a helper dictionary and is not consumed by normal source generation.
- Desired proposal state after this issue: replayed accepted callback code facts produce scoped source output through the normal renderer/source pipeline.

## Protocol Delta

- Adds: normal render/source pipeline support for accepted callback code classification.
- Changes: accepted callback facts can produce actual generated-source changes.
- Replaces: helper-only `callback_render_effect` if it is not wired.
- Deletes: duplicate render-effect helper path if obsolete.
- Leaves out of scope: verifier artifact production beyond local render tests, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: no render change without replayed accepted fact.
- Switched surface to v2: renderer/source export consumes accepted callback code facts.
- Deleted old surface path: helper-only render bypasses removed or made internal.
- User-visible behavior: generated source changes only inside accepted selected callback target range.

## Pandora Proof

- Target candidate: fixture accepted callback fact first; Pandora only if a real accepted fact exists.
- Evidence packet expected: accepted decision, replayed analysis fact, render plan/source diff, neighboring safety evidence.
- Decision behavior: renderer consumes accepted facts only.
- Command gate behavior: no direct render bypass without Decision Journal replay.
- Render effect: classify selected callback target as code or equivalent visible source improvement.
- Verifier/round-trip: exact round-trip required for output-affecting fixture/Pandora change.

## Implementation Slice

- C fact graph/query work: expose accepted callback fact to render/source planning in core path.
- Python/API/report work: wrap source diff evidence and command/report output.
- Journal/replay work: consume normal replay state from 017-070.
- Renderer/verifier work: implement scoped render projection in normal renderer.
- Tests: source diff is scoped, neighboring data/code unchanged, exact round-trip where output changes.

## Research Coverage

- [x] Normal source render path traced.
- [x] Accepted callback fact consumed by renderer.
- [x] Scoped render diff implemented.
- [x] Neighboring safety checked.
- [x] Exact round-trip run for output-affecting test.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] Render is not helper-only.
- [x] Render effect requires replayed accepted fact.
- [x] Neighboring data/code remains unchanged.
- [x] Proposal 017 updated with implementation findings.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-066` supersession addressed.
- [x] Code implemented in normal source/render pipeline.
- [x] Tests prove scoped render and negative safety.
- [x] Exact round-trip passes where output changes.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Notes

- Accepted callback decisions are projected through a temporary seeded-code entrypoint metadata overlay and rendered by `render_project_source_with_c_backend`.
- The verifier checks that the generated source changes and contains the selected callback symbol.
- The projection is read-only until an explicit verifier artifact write; it does not mutate target metadata or generated source output.

## Completion Evidence

- Focused tests: `uv run python -m pytest tests\test_reversing_loop.py tests\test_callback_slot_report.py -q` (`385 passed`).
- Required validation: `uv run python -m amiga_reversing.tools.validate_017_issues`.
- Whitespace check: `git diff --check`.
