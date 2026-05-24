# 017-071: Callback Render Through Normal Source Pipeline

Status: active
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

- [ ] Normal source render path traced.
- [ ] Accepted callback fact consumed by renderer.
- [ ] Scoped render diff implemented.
- [ ] Neighboring safety checked.
- [ ] Exact round-trip run for output-affecting test.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] Render is not helper-only.
- [ ] Render effect requires replayed accepted fact.
- [ ] Neighboring data/code remains unchanged.
- [ ] Proposal 017 updated with implementation findings.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-066` supersession addressed.
- [ ] Code implemented in normal source/render pipeline.
- [ ] Tests prove scoped render and negative safety.
- [ ] Exact round-trip passes where output changes.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.
