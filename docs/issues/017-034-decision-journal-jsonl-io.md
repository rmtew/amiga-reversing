# 017-034: Decision Journal JSONL IO

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: Decision Journal durable storage boundary
- Current proposal state: `017-033` added an inactive
  `evidence-decision/v1` schema and validator. No per-target journal file is
  read or written.
- Desired proposal state after this issue: 017 has append-only
  `decision_journal.jsonl` read/write helpers that validate every record and
  whole-journal chain without replaying decisions into analysis facts.

## Protocol Delta

- Adds: read, append, and whole-chain validation for per-target
  `decision_journal.jsonl`.
- Changes: Decision Journal records can become durable target-local state.
- Replaces: none.
- Deletes: none.
- Leaves out of scope: replay into C facts, replacing Manual Action Log,
  enabling RSSET mutation, rendering, command-gate activation, UI, broad
  migration.

## Default Behavior

- Unchanged by default: no existing report, planner, command, render, verifier,
  or Manual Action Log path may start consuming Decision Journal files.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: only explicit internal/dev helpers or tests may read
  or append the journal.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence packet expected: use the `017-032` packet shape as the referenced
  evidence for sample accept/defer/reject journal records.
- Decision behavior: a valid record can be appended, read back, and validated
  as part of an append-only chain, but must not affect analysis or command
  gates.
- Command gate behavior: Pandora RSSET remains blocked after journal IO.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification required; prove no
  source/render path changed.

## Implementation Slice

- C fact graph/query work: none.
- Python/API/report work: add focused file IO helpers for journal read, append,
  malformed JSONL diagnostics, and chain validation.
- Journal/replay work: append-only storage only. Do not apply accepted facts.
- Renderer/verifier work: none.
- Tests: append valid record, read back records, reject invalid append, report
  malformed JSONL, detect bad `prev`, detect duplicate IDs, preserve
  supersession validation, and prove no `manual_actions.jsonl` or command gate
  mutation occurs.

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

- [x] Existing target-local state file handling checked.
- [x] Current Manual Action Log append/read behavior checked for reusable IO
  patterns and replacement boundaries.
- [x] Decision Journal schema/hash-chain behavior checked against `017-033`.
- [x] Error/diagnostic shape for malformed JSONL and invalid records defined.
- [x] Side-effect boundary checked so journal IO cannot mutate analysis,
  reports, commands, render output, or Manual Action Log.

If research discovers another relevant subsystem, add it to this checklist
before continuing. The issue is not complete until the expanded checklist is
signed off or explicitly marked out of scope with reason.

## Research Review

- [x] Second pass checked every completed trace block against the named
  files/functions.
- [x] Cross-references searched for missed hooks, with search terms or commands
  recorded.
- [x] Findings were checked against the current RSSET packet and Decision
  Journal schema.
- [x] Proposal updated with concrete model corrections if journal IO changes
  the protocol.
- [x] Next issue scope follows from the implemented IO boundary.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Every checked research item has a trace block satisfying the Research
  Completion Standard.
- [x] Pandora report/verifier claims include reproducible command evidence, or
  explicitly not applicable because no Pandora command claim is made.
- [x] Journal IO tested for valid append/read and invalid input.
- [x] Decision/replay behavior tested where applicable, or explicitly deferred
  because this issue stores records only.
- [x] Command gate refuses unsafe mutation.
- [x] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Implementation Trace

### Target-Local State And Manual Action Boundary

- Files and functions inspected:
  - `amiga_reversing/reversing_workspace.py`
  - `_classify_file`
  - `clean_run_target_workspace`
  - `amiga_reversing/disasm/manual_actions.py`
  - `append_manual_action`
  - `project_manual_actions`
- Call/data flow summary: target hygiene already classifies target-local state
  and deletes local manual state during clean-run. `decision_journal.jsonl` is
  now classified as `LOCAL_MANUAL_STATE`, matching `manual_actions.jsonl`, so
  explicit journal IO can create durable target-local state without making the
  workspace unsafe as an unknown file. Manual Action Log append/projection
  remains separate and is not imported or called by Decision Journal IO.
- Current ownership boundary: Decision Journal JSONL is target-local state, but
  not active metadata projection state. Manual Action Log remains the active
  mutation path.
- Protocol/v2 implication: journal files can exist safely beside current state
  while replay remains deferred.
- Reuse/replace classification: reuse local-state hygiene classification; do
  not replace Manual Action Log.
- Commands or searches used:
  - `Get-Content amiga_reversing\reversing_workspace.py | Select-Object -First 285`
  - `Get-Content amiga_reversing\disasm\manual_actions.py | Select-Object -First 330`
- Open questions: none.

### JSONL Read/Append And Chain Validation

- Files and functions inspected:
  - `amiga_reversing/disasm/decision_journal.py`
  - `read_decision_journal`
  - `append_decision_record`
  - `decision_journal_next_prev`
  - `validate_decision_journal_records`
  - `decision_record_hash`
- Call/data flow summary: `read_decision_journal` parses non-empty JSONL lines,
  returns records plus diagnostics, and runs whole-journal schema/hash-chain
  validation. `append_decision_record` first validates the existing journal,
  then validates the candidate appended chain, and only then appends one sorted
  JSON line. Invalid existing state or invalid proposed records are returned as
  `status=rejected` and do not write.
- Current ownership boundary: IO writes only `decision_journal.jsonl`; it does
  not call report, planner, command, render, verifier, C analysis, or Manual
  Action Log APIs.
- Protocol/v2 implication: durable records now exist, but active replay is still
  absent by design.
- Reuse/replace classification: extend the 017-033 validator with file IO; no
  existing surface is switched to v2.
- Commands or searches used:
  - `Select-String -Path amiga_reversing\**\*.py,tests\*.py,docs\**\*.md -Pattern "decision_journal|Decision Journal|evidence-decision/v1|supersede_decision" -Context 1,2`
- Open questions: none.

### Diagnostics And Side-Effect Tests

- Files and functions inspected:
  - `tests/test_decision_journal.py`
  - `tests/test_reversing_workspace.py`
- Call/data flow summary: tests cover valid append/read, invalid append
  rejection without writing, malformed JSONL diagnostics, bad `prev`, duplicate
  ids, supersession validation, local-state hygiene classification, clean-run
  deletion behavior, and no command-gate or Manual Action Log mutation.
- Current ownership boundary: tests prove journal IO is explicit-only and
  side-effect free outside its own file.
- Protocol/v2 implication: invalid journals are inspectable diagnostics, not
  active analysis facts.
- Reuse/replace classification: no old code deleted; replay/cutover remains a
  future issue.
- Commands or searches used:
  - `uv run python -m pytest tests\test_decision_journal.py tests\test_reversing_workspace.py -q`
  - `uv run ruff check amiga_reversing\disasm\decision_journal.py amiga_reversing\reversing_workspace.py tests\test_decision_journal.py tests\test_reversing_workspace.py`
- Open questions: none.

### Pandora Proof

Pandora RSSET report command:

```powershell
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; $target='amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'; $json = uv run python -m amiga_reversing.reversing_loop rsset-candidate-report --target $target; $rep = $json | ConvertFrom-Json; $top = $rep.rsset_candidate_report.candidates[0]; Write-Output ('rsset safe_to_mutate=' + $rep.safe_to_mutate); Write-Output ('top_id=' + $top.candidate_id); Write-Output ('top_status=' + $top.status); Write-Output ('top_selected_addr={0:X8}' -f $top.selected_use.addr); Write-Output ('top_missing_gates=' + ($top.missing_gates -join ',')); Write-Output ('top_accepted_base_evidence_count=' + $top.evidence_search.accepted_base_evidence_count)
```

Commit: `363e0b587b4cfa54bbf53411147f9987fbf7f3e0`

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
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run python -m pytest tests\test_decision_journal.py tests\test_reversing_workspace.py -q
22 passed

$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run ruff check amiga_reversing\disasm\decision_journal.py amiga_reversing\reversing_workspace.py tests\test_decision_journal.py tests\test_reversing_workspace.py
All checks passed!
```

### Review Notes

- Default behavior impact: reports, planner, commands, render/export,
  verifier, and Manual Action Log do not read or apply Decision Journal records.
  Only explicit Decision Journal helpers read/append the file.
- Old code deletion: none. Manual Action Log replacement is still deferred.
- Decision/replay: durable storage and validation are tested; replay into C
  facts is deferred.
- Render/verifier/round-trip: not applicable because no output-affecting source
  or render path changed.
- Next issue scope: expose an internal validation/append surface for
  accept/defer/reject records from evidence packets, still without replay.
