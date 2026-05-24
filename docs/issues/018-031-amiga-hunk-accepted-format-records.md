# 018-031: Amiga HUNK Accepted Format Records

Status: active

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Blocked by: `docs/issues/018-030-executable-kb-restart-and-state-sync.md`
- Purpose: move a narrow Amiga HUNK executable-format slice from report-only
  inventory toward accepted or parser-asserted KB records where committed local
  citations already justify that status.
- This issue must not touch Mac parser/listing/web files.

## Knowledge Delta

Add or update only narrow Amiga HUNK facts that can be justified from committed
local knowledge:

- HUNK file identification;
- executable/object/library distinction where already documented;
- section/block roles needed by existing parser behavior;
- relocation or symbol-table facts only if the committed evidence is strong
  enough for accepted/parser-asserted status.

Facts without sufficient evidence must stay candidate/deferred/report-only with
explicit blocker reasons.

## Default Behavior

Default parser behavior should remain unchanged unless the change is validation
or reporting only. Do not rework Amiga import or rendering as part of this
issue.

## Evidence Standard

Accepted facts require committed source citations or parser assertions that
explain the standard interpretation. Candidate/deferred facts must not be
consumed as accepted parser authority.

## Implementation Slice

AFK slice:

- audit current Amiga HUNK knowledge and parser assumptions;
- update the platform executable KB with the smallest justified accepted or
  parser-asserted Amiga record;
- update tests/validators so unsupported promotions fail closed;
- update Proposal 018 observations with remaining Amiga gaps.

## Research Completion Standard

Complete only after a first-pass inventory and a second-pass review against
current parser behavior. If evidence is insufficient, complete by recording a
blocked/candidate result rather than forcing accepted facts.

## Research Coverage

- [ ] Current Amiga HUNK knowledge files checked.
- [ ] Existing HUNK parser/report behavior checked.
- [ ] Existing 018 Amiga report-only record checked.
- [ ] Citation strength reviewed for every promoted fact.
- [ ] Second-pass review checked for accidental parser behavior changes.

## Research Review

- [ ] Accepted/parser-asserted facts have citations or assertion rationale.
- [ ] Candidate/deferred facts are not consumed as accepted.
- [ ] Mac and Atari files were not changed.
- [ ] Proposal 018 records remaining Amiga gaps.

## Required Sign-Off

- [ ] KB validation passes.
- [ ] Targeted tests for platform executable formats pass.
- [ ] No source/render artifact churn was committed.

