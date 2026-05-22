# 017-032: Read-Only RSSET Evidence Packet Query

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: read-only v2 evidence packet/query slice
- Current proposal state: `017-031` completed the architecture inventory and
  recommended RSSET `rsset-raw-a6:022E` at `s0:000006E4` as the first v2
  packet/gate slice.
- Desired proposal state after this issue: 017 has a validated first packet
  shape for selected identity, evidence lanes, blockers/conflicts, render
  intent, and blocked command-gate summary, with any model corrections recorded.

## Protocol Delta

- Adds: internal read-only v2 evidence packet/query shape for one RSSET
  selected use.
- Changes: current RSSET report evidence can be projected into a common
  protocol packet shape for the selected candidate.
- Replaces: none.
- Deletes: none.
- Leaves out of scope: Decision Journal writes, accepted app-base evidence
  recording, source mutation, default report replacement, Manual Action Log
  cutover, broad Pandora mutation runs.

## Default Behavior

- Unchanged, v2 internal only: packet/query is read-only and must not change
  existing report, planner, command, render, or verifier behavior.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: none unless a new explicitly internal/dev report or
  test fixture is added.

## Pandora Proof

- Target candidate: `rsset-raw-a6:022E` at selected use `s0:000006E4`.
- Evidence packet expected: stable selected-use identity, candidate id,
  candidate family, evidence lanes, blockers, conflict state, render intent,
  and command-gate summary.
- Decision behavior: no accept/defer/reject write in this issue; packet may
  describe available future decisions only as read-only metadata.
- Command gate behavior: gate remains blocked because accepted app-base
  evidence, selected A6 base identity, selected-use path/lifetime scope, and
  explicit empty conflicts are missing.
- Render effect: none; render intent may be represented, but no source output
  changes.
- Verifier/round-trip: no output-affecting verification required; existing
  Pandora report/dry-run proof must show no mutation became available.

## Implementation Slice

- C fact graph/query work: add only the minimum internal query/identity support
  needed for the selected RSSET packet, or explicitly document why the first
  slice is a Python adapter over current C listing facts.
- Python/API/report work: expose or test the read-only packet shape without
  changing default reports/planner behavior.
- Journal/replay work: none, except schema placeholders for decision result
  references if needed by the packet model.
- Renderer/verifier work: none beyond proving no render/mutation path is
  exposed.
- Tests: focused tests for packet shape, selected identity stability, blocker
  mapping, conflict-state representation, and blocked command-gate summary.

## Research Completion Standard

If implementation discovers additional architecture facts, record them as trace
blocks with:

- files and functions inspected;
- call/data flow summary;
- current ownership boundary;
- protocol/v2 implication;
- reuse/replace classification where relevant;
- commands or searches used to check for missed hooks;
- open questions, or `none`.

Pandora report or verifier claims require reproducible evidence:

```text
Command:
Commit:
Target:
Key output:
Validation artifact path, or inline result block:
```

## Research Coverage

- [x] Current RSSET report payload fields mapped to packet fields, or marked
  out of scope with reason.
- [x] Selected identity source traced from listing/report data, or marked out
  of scope with reason.
- [x] Blocker/conflict mapping traced, or marked out of scope with reason.
- [x] Command-gate source traced, or marked out of scope with reason.
- [x] C/Python ownership boundary for this first packet documented, or marked
  out of scope with reason.

If research discovers another relevant subsystem, add it to this checklist
before continuing. The issue is not complete until the expanded checklist is
signed off or explicitly marked out of scope with reason.

## Research Review

- [x] Second pass checked every completed trace block against the named
  files/functions.
- [x] Cross-references searched for missed hooks, with search terms or commands
  recorded.
- [x] Findings were checked against Pandora current RSSET output with command
  output or validation artifact references.
- [x] Proposal updated with concrete model corrections if the packet model
  changed.
- [x] Next issue scope follows from the implemented packet slice.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Every checked research item has a trace block satisfying the Research
  Completion Standard.
- [x] Pandora report/verifier claims include reproducible command evidence.
- [x] Evidence packet shape tested.
- [x] Decision/replay behavior tested where applicable, or explicitly deferred
  because this issue is read-only.
- [x] Command gate refuses unsafe mutation.
- [x] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Implementation Trace

### Packet Field Mapping

- Files/functions inspected:
  - `amiga_reversing/reversing_loop.py`
  - `inspect_rsset_candidates`
  - `_listing_rsset_candidate_report`
  - `_rsset_candidate_group_summary`
  - `_rsset_candidate_evidence_search`
- Call/data flow summary: `inspect_rsset_candidates` opens listing rows,
  `_listing_rsset_candidate_report` groups A6 displacement uses, and
  `_rsset_candidate_group_summary` emits the selected use, same-displacement
  counts, app-slot context, evidence search, missing gates, command support, and
  report-only mutation policy. `query_rsset_evidence_packet` now adapts that
  report into an internal v2 packet without changing the source report.
- Current ownership boundary: Python owns this first read-only packet adapter
  and serialization. The underlying facts still come from the existing listing
  row/context pipeline; no new C fact graph/query API was added in this slice
  because the requested selected packet can be projected from current C-backed
  listing facts.
- Protocol/v2 implication: the first packet shape is validated without making
  the v2 model authoritative for all reports.
- Reuse/replace classification: reuse current RSSET report and command-support
  fields; do not replace default report/planner surfaces.
- Commands/searches used:
  - `Select-String -Path amiga_reversing\reversing_loop.py -Pattern "def inspect_rsset|def _listing_rsset|rsset_candidate|RSSET" -Context 2,4`
  - `Select-String -Path tests\test_reversing_loop.py -Pattern "rsset|candidate_report|packet|command_gate|safe_to_mutate" -Context 2,3`
- Open questions: none for this slice.

### Identity, Blockers, Conflicts, Gate

- Files/functions inspected:
  - `amiga_reversing/reversing_loop.py`
  - `_rsset_candidate_use_from_context`
  - `_rsset_candidate_selected_use_identity`
  - `_rsset_candidate_accepted_base_evidence_ref`
  - `_rsset_candidate_conflicts_rejection_reason`
  - `_rsset_candidate_evidence_matches_selected_use`
- Call/data flow summary: selected identity comes from listing element context
  fields `hunk`, `addr`, `operand_index`, `base_register`, `displacement`,
  `element_id`, and `stable_key`. Current evidence search can prove accepted
  base evidence only when selected-use identity, selected-use path/lifetime
  scope, selected A6 base id, and explicit empty conflicts all exist. The new
  packet expands the current single report gate `missing_accepted_base_evidence`
  into those v2 blockers while retaining the report source gate.
- Current ownership boundary: blocker/conflict interpretation is a read-only
  Python projection over existing report/evidence-search state.
- Protocol/v2 implication: conflicts have an explicit packet state. For
  `rsset-raw-a6:022E` it is `unknown`, `explicit_empty=false`, because no
  accepted selected-use RSSET app-base evidence exists.
- Reuse/replace classification: reuse existing stricter 017-029 conflict
  validation; do not add Decision Journal writes.
- Commands/searches used:
  - `Select-String -Path tests\test_reversing_loop.py -Pattern "def test_listing_rsset|rsset_candidate_report|missing_accepted_base_evidence" -Context 1,4`
  - `Get-Content amiga_reversing\reversing_loop.py | Select-Object -Skip 3620 -First 230`
- Open questions: none for this slice.

### Pandora Proof

Command:

```powershell
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; $target='amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'; $json = uv run python -m amiga_reversing.reversing_loop rsset-candidate-report --target $target; $rep = $json | ConvertFrom-Json; $top = $rep.rsset_candidate_report.candidates[0]; Write-Output ('rsset safe_to_mutate=' + $rep.safe_to_mutate); Write-Output ('rsset candidate_count=' + $rep.rsset_candidate_report.candidate_count); Write-Output ('rsset use_count=' + $rep.rsset_candidate_report.use_count); Write-Output ('top_id=' + $top.candidate_id); Write-Output ('top_status=' + $top.status); Write-Output ('top_selected_addr={0:X8}' -f $top.selected_use.addr); Write-Output ('top_missing_gates=' + ($top.missing_gates -join ',')); Write-Output ('top_accepted_base_evidence_count=' + $top.evidence_search.accepted_base_evidence_count)
```

Commit: `6ba4e31838ad7d98784da625d489d497055f7186`

Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`

Key output:

```text
rsset safe_to_mutate=False
rsset candidate_count=125
rsset use_count=994
top_id=rsset-raw-a6:022E
top_status=blocked
top_selected_addr=000006E4
top_missing_gates=missing_accepted_base_evidence
top_accepted_base_evidence_count=0
```

Dry-run command:

```powershell
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; $target='amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'; $json = uv run python -m amiga_reversing.reversing_loop run-one --target $target --dry-run; $rep = $json | ConvertFrom-Json; Write-Output ('dry_action=' + $rep.action); Write-Output ('dry_action_result_status=' + $rep.action_result.status); Write-Output ('dry_planner_status=' + $rep.planner.status); Write-Output ('dry_next_reason=' + $rep.next.reason)
```

Key output:

```text
dry_action=
dry_action_result_status=not_run
dry_planner_status=no_candidate
dry_next_reason=no locator-backed command candidate
```

Validation:

```text
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run python -m pytest tests\test_reversing_loop.py -q -k "rsset_evidence_packet or rsset_candidate_report"
12 passed, 312 deselected

$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run ruff check amiga_reversing\reversing_loop.py tests\test_reversing_loop.py
All checks passed!
```

### Review Notes

- Default report/planner behavior impact: unchanged. Tests assert the packet is
  not embedded into `rsset_candidate_report`, and Pandora dry run still reports
  `no_candidate`.
- Old code deletion: none; no old surface path was replaced in this issue.
- Decision/replay: explicitly deferred because this issue is read-only.
- Render/verifier/round-trip: not applicable because no output-affecting
  mutation or source rendering change was introduced.
- Next issue scope: add Decision Journal accept/defer/reject records for this
  packet shape, then gate `rsset.binding.bind` only from accepted packet-backed
  evidence.
