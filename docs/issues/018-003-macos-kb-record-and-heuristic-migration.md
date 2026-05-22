# 018-003: Mac OS KB Record And Heuristic Migration

Status: open

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: accepted Mac OS executable-format KB records
- Blocked by: `018-001`, `018-002`
- Current proposal state: Mac evidence packets may exist, but accepted KB
  records and migration rules for the current heuristic parser are not in place.
- Desired proposal state after this issue: the Mac CODE/resource facts needed by
  012 are represented in the executable-format KB, and current heuristic
  behavior is explicitly downgraded, validated, or replaced.

## Knowledge Delta

- Adds: Mac OS executable-format KB records for MPW `Asm` / application-style
  CODE resources.
- Changes: current CODE entry handling is mapped to KB fact states and parser
  behavior.
- Replaces: implicit `movea.l (a7)+,a0` acceptance with cited or explicitly
  candidate KB behavior.
- Deletes: none unless stale Mac KB assertions are replaced.
- Leaves out of scope: parser/listing migration, Amiga/Atari records, and full
  non-CODE resource semantics.

## Default Behavior

- No parser behavior changes.
- No renderer behavior changes.
- Existing artifact remains valid only as current output, not as proof of
  accepted executable facts.

## Evidence Standard

- Validated records require citations from 018-002.
- Parser assertions require reason, indirect evidence, standard interpretation,
  and review status.
- Candidate records may describe observed bytes and possible meanings, but must
  not authorize accepted code/data/entry classification.

## Migration Requirement

For the current `movea.l (a7)+,a0` CODE boundary:

- either validate it with cited Segment Loader/MPW output facts;
- or replace it with a documented entrypoint rule;
- or record it as `candidate` and ensure later parser/listing work cannot treat
  it as confirmed.

## Implementation Slice

- KB data: update `knowledge/platform_executable_formats.json`.
- Docs: update `docs/platform-executable-formats.md` with Mac interpretation.
- Tests: validate Mac KB records and fact-state transitions.
- Proposal: update 012 blocker status if and only if accepted facts now exist.
- No parser/listing code changes in this issue.

## Research Completion Standard

Record trace blocks for every accepted Mac fact id, cited source, assertion,
candidate, conflict, and deferred area.

## Research Coverage

- [ ] 018-002 citation packets reviewed.
- [ ] Mac archetype ids and format ids checked.
- [ ] MPW producer/variant scope checked.
- [ ] Entrypoint fact states assigned.
- [ ] CODE 0 and nonzero CODE fact states assigned.
- [ ] Unknown/conflict/deferred records created.

## Research Review

- [ ] Second pass checked Mac KB records against citation packets.
- [ ] Candidate facts cannot be mistaken for accepted facts.
- [ ] Parser assertion records have reason and standard interpretation.
- [ ] Proposal 012 blocker text updated or deliberately left blocked.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Mac KB records added and schema-valid.
- [ ] `movea.l (a7)+,a0` migration requirement resolved.
- [ ] Tests validate fact states and citation references.
- [ ] No parser or renderer behavior changed.
- [ ] Post-commit review found no unresolved worthwhile findings.
