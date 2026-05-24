# 017-057: Source-Offset Immediate Provenance Unblocker

Status: completed
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: source-offset immediate provenance.
- Current proposal state: 9 source-offset-looking immediate candidates remain report-only; `s0:000009A6:op0` is durably deferred by the Decision Journal lane added in the historical 017 sequence.
- Desired proposal state after this issue: one exact source-offset immediate is re-evaluated from current evidence, and the missing proof for promotion is explicit.

## Protocol Delta

- Adds: a current read-only provenance packet review for one exact source-offset immediate, preferably `s0:000009A6:op0`.
- Changes: proposal living notes with whether the blocker is policy, missing runtime-address provenance, missing dataflow, width/signedness ambiguity, landing-range ambiguity, or verifier/render support.
- Replaces: no existing protocol model.
- Deletes: nothing.
- Leaves out of scope: mutation, source edits, Manual Action Log writes, Decision Journal writes, verifier artifact writes, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: source-offset immediate packets remain read-only unless a later issue proves accepted evidence and adds gates.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: current report-only behavior must remain unless a separate mutation issue is created later.

## Pandora Proof

- Target candidate: `s0:000009A6:op0` / `addi.w #4224,d1`, unless current reports show a stronger exact candidate.
- Evidence packet expected: selected operand identity, literal value, width, signedness, possible source-offset interpretation, landing range, dataflow use, conflicts, current Decision Journal lane, blockers, and render/verifier readiness.
- Decision behavior: no accept decision in this issue; update only blocker/defer explanation.
- Command gate behavior: `immediate_ref.interpret` must remain disabled for same-literal/source-offset-only evidence.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification unless support code changes.

## Implementation Slice

- C fact graph/query work: none unless current row/dataflow lookup is demonstrably incomplete for this packet.
- Python/API/report work: inspect existing `source-offset-immediate-packet` and immediate-reference report output; add only read-only blocker detail if needed.
- Journal/replay work: inspect existing deferred lane; do not append.
- Renderer/verifier work: none.
- Tests: focused packet/report tests if output shape changes; otherwise document the current evidence.

## Research Coverage

- [x] Current immediate-reference report rerun for Pandora.
- [x] Current `source-offset-immediate-packet` inspected for the selected candidate.
- [x] Current Decision Journal lane checked without appending.
- [x] Landing/dataflow evidence checked.
- [x] Conflict state checked.
- [x] Render/verifier readiness checked as read-only.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] Confirmed source-offset-only evidence remains non-accepting unless stronger provenance exists.
- [x] Confirmed command gate remains disabled.
- [x] Confirmed no source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified.
- [x] Proposal 017 living notes updated with concise findings.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] One exact operand selected.
- [x] Blockers/conflicts recorded explicitly.
- [x] Output remains read-only.
- [x] Any support-code change is tied to a concrete packet/report correctness blocker.
- [x] Focused tests pass if code changes.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

Pandora target:
`amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.

Read-only commands rerun:

- `uv run python -m amiga_reversing.reversing_loop immediate-ref-report --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
- `uv run python -m amiga_reversing.reversing_loop source-offset-immediate-packet --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 --candidate-id immediate-runtime-ref:s0:000009A6:instruction:664:0:00001080`
- `uv run python -m amiga_reversing.reversing_loop decision-journal-report --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`

Selected operand:

- Packet id:
  `source-offset-immediate-packet:immediate-runtime-ref:s0:000009A6:instruction:664:0:00001080`.
- Selected identity: `s0:000009A6:op0`, hunk 0, addr 2470,
  operand index 0.
- Instruction: `addi.w #4224,d1`.
- Literal: value 4224 / `$1080`, width 16 bits / 2 bytes,
  signedness unknown.
- Possible interpretation: source offset 4224 by range match only, no runtime
  address provenance.

Evidence state:

- Landing range is inside the loaded binary but classification remains
  `unknown`.
- Local dataflow is listing-instruction-only; downstream dataflow query is
  unavailable.
- Same-literal context is explicitly report-only and does not prove
  source-offset provenance.
- Conflicts are explicit and empty.
- Decision Journal lane is `deferred` by
  `decision-source-offset-immediate-000009a6-defer-017-046`, with no active
  accepted decision.

Blockers:

- `same_literal_only_not_durable_provenance`
- `missing_accepted_runtime_address_provenance`
- `missing_source_offset_decision_replay_support`
- `missing_source_offset_render_verifier_gate`

Command/render state:

- `immediate_ref.interpret` remains disabled for this packet:
  `candidate_command_available=false`, `enabled=false`,
  `safe_to_mutate=false`.
- Render intent remains analysis-only with `render_effect=none`.
- The precise defer reason is unchanged: source-offset-only evidence is
  plausible but non-accepting until accepted runtime-address provenance and
  source-offset replay/render/verifier gates exist.

No code changed, so no focused tests were required beyond issue validation and
diff checks.
