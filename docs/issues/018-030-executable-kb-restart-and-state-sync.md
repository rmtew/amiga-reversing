# 018-030: Executable KB Restart and State Sync

Status: active

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Purpose: restart the live 018 issue trail after completed issue files were
  consolidated/deleted, and produce the current authoritative state map for
  overnight worker planning.
- This issue is docs-only. It must not change parser behavior, generated facts,
  target artifacts, or platform KB records.
- Downstream issues in this batch depend on this issue for a clean done/open/
  blocked map.

## Knowledge Delta

Record the current 018 state in the issue and, if needed, with a small proposal
note:

- which Mac facts are accepted and parser-consumed;
- which Mac facts remain candidate, deferred, unsupported, or blocked;
- which Amiga and Atari records are report-only versus accepted;
- which generated-table and parser-coverage gaps remain;
- which 012 closeout blockers are still owned by 018.

Do not invent new citations or promote facts in this sync issue.

## Default Behavior

No runtime behavior changes. Current parser/listing/web behavior must remain
unchanged.

## Evidence Standard

Use only committed proposal text, committed KB files, current validator output,
current parser/report code, and current tests. If evidence conflicts, record the
conflict instead of resolving it by assumption.

## Implementation Slice

AFK/docs-only slice:

- review Proposal 018 and Proposal 012 closeout text;
- review `knowledge/platform_executable_formats.json`;
- review current platform executable validator/report commands;
- record a done/open/blocked matrix;
- list exact next issues and dependency edges.

## Research Completion Standard

This issue is not complete until the worker has checked the proposal text, KB
file, validator/report code, and relevant tests at least twice: once for broad
inventory and once for missed contradictions.

## Research Coverage

- [ ] Proposal 018 status and relationship-to-012 sections checked.
- [ ] Proposal 012 closeout matrix checked.
- [ ] Platform executable KB file checked.
- [ ] Platform executable validator/report code checked.
- [ ] Relevant tests checked.
- [ ] Second-pass contradiction review completed.

## Research Review

- [ ] Findings distinguish accepted facts from candidate/deferred facts.
- [ ] Findings distinguish live issue work from historical consolidated issue
  records.
- [ ] No parser, target artifact, generated file, or web behavior was changed.
- [ ] Dependency order for 018-031 through 018-035 and 012-023 was reviewed.

## Required Sign-Off

- [ ] The issue records the authoritative current 018 state.
- [ ] The issue identifies any proposal wording that would mislead a worker.
- [ ] The worker ran the available issue/KB validation commands or recorded why
  they could not run.

