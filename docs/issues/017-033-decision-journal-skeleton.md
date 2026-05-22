# 017-033: Decision Journal Skeleton

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: Decision Journal durable decision model
- Current proposal state: `017-032` added a read-only RSSET evidence packet
  projection with selected identity, blockers/conflicts, render intent, and a
  blocked command gate. No accepted/deferred/rejected decisions are stored yet.
- Desired proposal state after this issue: 017 has a validated first Decision
  Journal schema and append/supersession model that can reference the RSSET
  packet shape without becoming active replay or mutation authority.

## Protocol Delta

- Adds: per-target Decision Journal record schema for `accept_fact`,
  `defer_fact`, `reject_fact`, and `supersede_decision`.
- Changes: evidence packets can be referenced by durable decision records, but
  remain read-only unless later replay work consumes those decisions.
- Replaces: none.
- Deletes: none.
- Leaves out of scope: applying decisions to the C fact graph, replacing Manual
  Action Log, enabling RSSET mutation, rendering, command-gate activation,
  default behavior changes, legacy migration.

## Default Behavior

- Unchanged, v2 internal only: journal schema/tests must not affect current
  reports, planner, commands, render/export, Manual Action Log, or verifier
  behavior.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: none unless an explicitly internal/dev validation
  helper is added.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence packet expected: existing `017-032` packet shape is referenced by
  decision records through selected identity, candidate id, and evidence refs.
- Decision behavior: records validate structurally for accept/defer/reject and
  supersession, but are not applied to analysis or command gates yet.
- Command gate behavior: remains blocked; journal records must not expose
  `rsset.binding.bind`.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification required; tests must
  prove journal validation is side-effect free.

## Implementation Slice

- C fact graph/query work: none, unless a tiny type placeholder is needed and
  documented as inactive.
- Python/API/report work: schema/validator helpers and focused tests only.
- Journal/replay work: define record shape, required fields, actor metadata,
  selected identity reference, evidence refs, conflict state, supersession
  reference shape, and validation diagnostics. Do not add active replay.
- Renderer/verifier work: none.
- Tests: schema validation for valid/invalid accept/defer/reject/supersede
  records; proof that no command gate or mutation behavior changes.

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

- [x] Current Manual Action Log append/validation boundaries checked, or marked
  out of scope with reason.
- [x] Decision Journal record fields mapped to `017-032` RSSET packet fields,
  or marked out of scope with reason.
- [x] Supersession and invalid-record diagnostics shape defined, or marked out
  of scope with reason.
- [x] Side-effect boundary checked so journal validation cannot mutate reports,
  commands, or target state, or marked out of scope with reason.

If research discovers another relevant subsystem, add it to this checklist
before continuing. The issue is not complete until the expanded checklist is
signed off or explicitly marked out of scope with reason.

## Research Review

- [x] Second pass checked every completed trace block against the named
  files/functions.
- [x] Cross-references searched for missed hooks, with search terms or commands
  recorded.
- [x] Findings were checked against the current RSSET packet shape.
- [x] Proposal updated with concrete model corrections if the journal model
  changed.
- [x] Next issue scope follows from the journal skeleton.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Every checked research item has a trace block satisfying the Research
  Completion Standard.
- [x] Pandora report/verifier claims include reproducible command evidence, or
  explicitly not applicable because no Pandora command claim is made.
- [x] Decision record schema tested.
- [x] Decision/replay behavior tested where applicable, or explicitly deferred
  because this issue defines schema only.
- [x] Command gate refuses unsafe mutation.
- [x] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Implementation Trace

### Manual Action Log Boundary

- Files and functions inspected:
  - `amiga_reversing/disasm/manual_actions.py`
  - `manual_action_log_path`
  - `append_manual_action`
  - `project_manual_actions`
  - `validate_manual_action_payload`
  - `amiga_reversing/reversing_workspace.py`
  - `_classify_target_file`
- Call/data flow summary: the Manual Action Log writes `manual_actions.jsonl`
  through `append_manual_action`, validates target identity and reserved fields,
  and feeds projected manual state through `project_manual_actions`. Target
  hygiene treats `manual_actions.jsonl` as local manual state. 017-033 does not
  import, call, or replace those paths.
- Current ownership boundary: Manual Action Log remains the active mutation and
  metadata projection path. Decision Journal is an inactive schema/validation
  module only.
- Protocol/v2 implication: v2 can reuse JSONL/path/hash-chain ideas without
  making the journal active replay authority yet.
- Reuse/replace classification: reuse append-only audit concepts; replace
  nothing in this issue.
- Commands or searches used:
  - `Select-String -Path amiga_reversing\**\*.py,tests\*.py -Pattern "Decision Journal|decision_journal|accept_fact|defer_fact|reject_fact|manual_action_log|manual_actions.jsonl" -Context 1,3`
  - `Get-Content amiga_reversing\disasm\manual_actions.py | Select-Object -First 330`
  - `Get-Content amiga_reversing\disasm\manual_actions.py | Select-Object -Skip 2020 -First 120`
- Open questions: none.

### Journal Schema And Packet Mapping

- Files and functions inspected:
  - `amiga_reversing/disasm/decision_journal.py`
  - `decision_packet_reference`
  - `validate_decision_record`
  - `validate_decision_journal_records`
  - `decision_record_hash`
  - `tests/test_decision_journal.py`
- Call/data flow summary: `decision_packet_reference` maps an 017-032 packet
  into `packet_id`, `candidate_id`, `selected_identity`, and `evidence_refs`.
  `validate_decision_record` validates common record fields, actor metadata,
  selected identity, evidence refs, conflict state, action-specific accept,
  defer, reject, and supersede fields. `validate_decision_journal_records`
  validates append-only `prev` hashes, duplicate ids, and supersession targets
  against earlier decisions.
- Current ownership boundary: Python owns the schema skeleton and validation
  diagnostics. C fact graph replay, active fact projection, command-gate
  activation, and rendering remain out of scope.
- Protocol/v2 implication: Decision Journal records can now durably reference
  the RSSET packet shape without becoming active evidence.
- Reuse/replace classification: new parallel v2 helper; no default report,
  planner, command, render, verifier, or Manual Action Log path is replaced.
- Commands or searches used:
  - `Select-String -Path amiga_reversing\**\*.py,tests\*.py,docs\**\*.md -Pattern "decision_journal|Decision Journal|evidence-decision/v1|supersede_decision" -Context 1,2`
- Open questions: none.

### Supersession And Diagnostics Shape

- Files and functions inspected:
  - `amiga_reversing/disasm/decision_journal.py`
  - `_decision_record_diagnostics`
  - `_diagnostic`
  - `validate_decision_journal_records`
- Call/data flow summary: diagnostics are structured objects with `field`,
  `message`, and journal `index` when validating a sequence. Supersession uses
  `action=supersede_decision`, `supersedes_decision_id`, optional
  `replacement_decision_id`, and `reason`; the validator rejects forward or
  missing supersession targets.
- Current ownership boundary: diagnostics are validation output only; they do
  not create review items or mutate state.
- Protocol/v2 implication: invalid decisions can remain inspectable without
  being applied.
- Reuse/replace classification: new schema-level diagnostic shape.
- Commands or searches used:
  - `uv run python -m pytest tests\test_decision_journal.py -q`
- Open questions: none.

### Side-Effect Boundary And Pandora Proof

- Files and functions inspected:
  - `tests/test_decision_journal.py`
  - `test_decision_journal_validation_is_side_effect_free`
  - `amiga_reversing/reversing_loop.py`
  - `query_rsset_evidence_packet`
- Call/data flow summary: tests validate that journal validation does not write
  `decision_journal.jsonl`, does not write `manual_actions.jsonl`, and does not
  alter the blocked RSSET packet command gate.
- Current ownership boundary: journal validation reads in-memory records only.
- Protocol/v2 implication: 017-033 adds record validation, not active replay or
  mutation.
- Reuse/replace classification: no old code deleted; deletion is deferred until
  later v2 replay/cutover issues.
- Commands or searches used:
  - `uv run ruff check amiga_reversing\disasm\decision_journal.py tests\test_decision_journal.py`
- Open questions: none.

Pandora RSSET report command:

```powershell
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; $target='amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'; $json = uv run python -m amiga_reversing.reversing_loop rsset-candidate-report --target $target; $rep = $json | ConvertFrom-Json; $top = $rep.rsset_candidate_report.candidates[0]; Write-Output ('rsset safe_to_mutate=' + $rep.safe_to_mutate); Write-Output ('top_id=' + $top.candidate_id); Write-Output ('top_status=' + $top.status); Write-Output ('top_selected_addr={0:X8}' -f $top.selected_use.addr); Write-Output ('top_missing_gates=' + ($top.missing_gates -join ',')); Write-Output ('top_accepted_base_evidence_count=' + $top.evidence_search.accepted_base_evidence_count)
```

Commit: `febcbf667d439c42a934382c2174cbc12656684a`

Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`

Key output:

```text
rsset safe_to_mutate=False
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
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run python -m pytest tests\test_decision_journal.py -q
6 passed

$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run ruff check amiga_reversing\disasm\decision_journal.py tests\test_decision_journal.py
All checks passed!
```

### Review Notes

- Default behavior impact: unchanged. No existing runtime path imports or calls
  the new Decision Journal validator.
- Old code deletion: none. Manual Action Log cutover is explicitly deferred.
- Decision/replay behavior: record validation and chain/supersession validation
  are tested; active replay is deferred.
- Render/verifier/round-trip: not applicable because no output-affecting
  mutation or render path changed.
- Next issue scope: read/append the per-target journal file and expose internal
  accept/defer/reject validation without applying decisions to C facts.
