# 018-032: Atari ST PRG Accepted Format Records

Status: active

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Blocked by: `docs/issues/018-030-executable-kb-restart-and-state-sync.md`
- Purpose: move a narrow Atari ST PRG/TOS/TTP executable-format slice from
  report-only inventory toward accepted or parser-asserted KB records where
  committed local citations already justify that status.
- This issue must not touch Mac parser/listing/web files.

## Knowledge Delta

Add or update only narrow Atari ST facts that can be justified from committed
local knowledge:

- executable header identity and text/data/bss shape;
- relocation-table presence and parser-visible role where documented;
- symbol-table/debug records only if evidence is strong enough;
- TOS/TTP/PRG distinctions only where committed evidence supports them.

Facts without sufficient evidence must stay candidate/deferred/report-only with
explicit blocker reasons.

## Default Behavior

Default parser behavior should remain unchanged unless the change is validation
or reporting only. Do not rework Atari import or rendering as part of this
issue.

## Evidence Standard

Accepted facts require committed source citations or parser assertions that
explain the standard interpretation. Candidate/deferred facts must not be
consumed as accepted parser authority.

## Implementation Slice

AFK slice:

- audit current Atari executable knowledge and parser assumptions;
- update the platform executable KB with the smallest justified accepted or
  parser-asserted Atari record;
- update tests/validators so unsupported promotions fail closed;
- update Proposal 018 observations with remaining Atari gaps.

## Research Completion Standard

Complete only after a first-pass inventory and a second-pass review against
current parser behavior. If evidence is insufficient, complete by recording a
blocked/candidate result rather than forcing accepted facts.

## Research Coverage

- [ ] Current Atari ST executable knowledge files checked.
- [ ] Existing Atari parser/report behavior checked.
- [ ] Existing 018 Atari report-only record checked.
- [ ] Citation strength reviewed for every promoted fact.
- [ ] Second-pass review checked for accidental parser behavior changes.

## Research Review

- [ ] Accepted/parser-asserted facts have citations or assertion rationale.
- [ ] Candidate/deferred facts are not consumed as accepted.
- [ ] Mac and Amiga files were not changed.
- [ ] Proposal 018 records remaining Atari gaps.

## Required Sign-Off

- [ ] KB validation passes.
- [ ] Targeted tests for platform executable formats pass.
- [ ] No source/render artifact churn was committed.

