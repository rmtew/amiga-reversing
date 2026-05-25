# 017-074: Pandora Disk/Subtarget Listing Resolution

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: making real Pandora callback-derived source improvement possible after the command/replay/render/verifier path was implemented.
- Current proposal state: `017-073` proved callback decisions work when a current packet exists, but the real Pandora disk-level target blocks at `listing_open.status=failed`.
- Desired proposal state after this issue: the Pandora disk-level target either resolves to the correct disassemblable subtarget listing for callback packet selection, or the report exposes a precise, actionable structural blocker that explains why disk-level callback analysis cannot proceed.

## Protocol Delta

- Adds: a source-backed listing resolution path from the Pandora disk/container target to the rendered subtarget used by 017.
- Changes: callback packet selection must not fail merely because the user-facing target is a container when the proposal already names a concrete disassemblable subtarget.
- Replaces: the vague disk-level `listing_open.status=failed` endpoint from `017-073`.
- Leaves out of scope: speculative callback acceptance, broad code seeding, unrelated target cleanup, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Container targets with one or more disassemblable subtargets should expose enough structured context for 017 reports to select the intended subtarget listing.
- If automatic subtarget selection would be ambiguous, the report must fail closed with candidate subtarget identities and a clear next action.
- If no disassemblable subtarget exists, the report must fail closed with that fact and no source or journal mutation.
- Unsafe or unresolved callback candidates must remain non-mutating.

## Pandora Proof

- Container target: `targets\amiga_disk_pandora-1988-firebird`
- Expected subtarget: `amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
- Expected rendered listing:
  `targets\amiga_disk_pandora-1988-firebird\targets\amiga_raw_pandora_3e1ee0f1_bk_00_000000e8\pandora_3e1ee0f1_bk_00_000000e8.s`
- Evidence packet expected: callback report output that either reads the expected subtarget listing or reports a precise ambiguity/missing-listing blocker.
- Decision behavior: no Decision Journal write unless a current packet passes all existing callback gates.
- Render effect: only if a real candidate becomes accepted through the existing verifier path.
- Verifier/round-trip: mandatory for any output change.

## Implementation Slice

- C fact graph/query work: do not bypass existing C/export ownership; if listing selection needs source metadata, expose it through the normal target/project metadata path rather than ad hoc path guesses.
- Python/API/report work: update the callback report/listing open path so a disk/container target can resolve the relevant subtarget listing or report structured ambiguity.
- Journal/replay work: unchanged except that any newly actionable callback candidate must still use `callback-decision` and Decision Journal replay.
- Renderer/verifier work: unchanged except that any source-changing result must use the existing normal C backend render and `decision-verifier-artifact` gates.
- Tests: add focused fixture coverage for container-to-subtarget listing resolution and the ambiguous/no-listing closed-failure cases.

## Research Coverage

- [ ] Current Pandora target/subtarget metadata inspected.
- [ ] Existing project path resolution behavior understood before changing it.
- [ ] Callback report can open the expected Pandora subtarget listing, or reports a precise structural blocker.
- [ ] Ambiguous container selection fails closed with candidate subtarget identities.
- [ ] Missing subtarget/listing fails closed without Decision Journal, metadata, generated source, or verifier artifact writes.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] The result is not a helper-only bypass; normal target/project resolution is used.
- [ ] Any real Pandora candidate exposed by the fixed listing path is either processed through the existing callback gates or explicitly deferred by those gates.
- [ ] No source write occurs without verifier artifact and exact round-trip success.
- [ ] Proposal 017 living notes updated with the real outcome.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-073` completion notes checked before work.
- [ ] Focused tests cover success and closed-failure listing resolution.
- [ ] Real Pandora callback report rerun.
- [ ] Exact round-trip passes for any source change.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.
