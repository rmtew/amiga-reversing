# 017-087: Render Accepted A5 Hardware References

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: `017-086` must be complete first.
- Protocol area: source rendering from accepted A5 hardware-reference facts.
- Current proposal state: A5 decisions can be made only after `017-086`, but accepted facts still need normal source output consumption.
- Desired proposal state after this issue: accepted A5 hardware-reference facts render through the normal source pipeline in Amiga-style, vasm-compatible source.

## Protocol Delta

- Adds: C/backend source rendering for accepted A5 hardware-reference metadata.
- Changes: accepted A5 uses can improve source readability without changing bytes.
- Replaces: raw anonymous A5 operands where accepted evidence proves a hardware-register interpretation.
- Leaves out of scope: accepting new decisions, verifier artifact writing, speculative unknown-use promotion, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- Render only accepted replayed A5 facts.
- Use existing Amiga hardware naming conventions and `knowledge/amiga-hardware.md`; do not invent new register names or assembler syntax.
- Output must remain vasm-compatible and exact-round-trip safe.
- Unknown, stale, or ambiguous A5 uses must render exactly as before.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.
- Use the same tracer-bullet A5 decision from `017-086`.
- Expected result: source output changes only for the accepted A5 use site or its directly authorized representation, and all unrelated A5 uses remain unchanged.

## Implementation Slice

- C fact graph/query work: expose accepted A5 metadata to source rendering using the same framework as other accepted manual facts.
- Python/API/report work: keep report state synchronized with rendered/not-rendered status.
- Journal/replay work: consume `017-086` replay output only.
- Renderer/verifier work: implement normal source rendering and keep assembler compatibility.
- Tests: rendered accepted use, unknown use unchanged, stale metadata ignored, exact round-trip fixture or real-target check.

## Research Coverage

- [ ] Existing Amiga hardware rendering conventions checked.
- [ ] `knowledge/amiga-hardware.md` used for symbol naming.
- [ ] Accepted replayed fact is the only source of rendering authority.
- [ ] Unknown A5 uses remain byte-identical in rendered source.
- [ ] Assembler compatibility and exact round-trip constraints checked.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] This changes source output only when accepted evidence authorizes it.
- [ ] The rendering path is normal framework extension, not a target-specific special case.
- [ ] No backwards-compatibility shim or legacy workaround is added.
- [ ] Proposal 017 living notes updated with the implementation result.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-086` complete.
- [ ] Focused source-render tests pass.
- [ ] Real Pandora render diff is narrow and explained.
- [ ] Exact round-trip passes for affected output.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

