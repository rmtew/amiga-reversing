# 018-026: Mac OS Byte-Entry Rule Resolution

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS CODE byte-entry rules and parser authority
- Blocked by: `018-021`, `018-025`
- Work order: do before any issue that promotes Mac CODE entrypoints from
  candidate to accepted. May run in parallel with research-only issues
  `018-027`, `018-028`, and `018-029` if it does not touch shared parser/render
  files until those are complete.
- Current proposal state: the observed `movea.l (a7)+,a0` boundary remains
  candidate-only. Mac previews/listings are useful, but full Proposal 012
  closeout is blocked because byte-entry rules are not accepted or
  parser-asserted executable-format knowledge.
- Desired proposal state after this issue: the byte-entry rule is either
  validated/parser-asserted with sufficient evidence and migrated into parser
  output, or explicitly remains candidate/deferred with a documented blocker and
  no misleading parser promotion.

## Knowledge Delta

- Adds: final decision packet for Mac CODE byte-entry authority.
- Changes: current byte-entry heuristic is either accepted/parser-asserted or
  explicitly retained as candidate/deferred with a next blocker.
- Replaces: vague future byte-entry closeout note.
- Deletes: no candidate evidence unless replaced by stronger evidence.
- Leaves out of scope: relocation/fixup application, source-to-CODE mapping,
  non-CODE semantics, and byte-for-byte roundtrip.

## Default Behavior

- Do not promote `movea.l (a7)+,a0` just because it works on MPW `Asm`.
- Accepted/parser-asserted byte-entry facts must cite allowed sources or include
  explicit parser-assertion reason, standard interpretation, scope, and review
  status.
- If evidence is insufficient, keep parser output candidate/deferred and close
  this issue only as a documented blocker decision.
- CODE 0 remains metadata-only.
- Existing selected CODE 1 and candidate preview behavior must not regress.

## Evidence Standard

- Evidence must cover nonzero CODE resource headers, CODE 1 startup, jump-table
  entry relationships, and any claimed executable-byte start rule.
- Project-observed byte patterns may support candidates, not accepted general
  rules.
- Parser-output validation must prove emitted fact ids/status/parser-use match
  the KB.
- Tests must prove candidate/deferred state is preserved if no promotion occurs.

## Implementation Slice

- Search local Mac/MPW docs and existing KB packets for byte-entry evidence.
- Decide one of:
  - accepted/parser-asserted byte-entry migration, with parser/listing tests; or
  - explicit deferred blocker record, with no parser behavior change.
- Update `knowledge/platform_executable_formats.json` and docs accordingly.
- If parser output changes, update generated/runtime fact consumers and
  relevant payload/artifact/web tests.
- Regenerate MPW `Asm` artifact if rendered output changes.

## Research Completion Standard

Record trace blocks for:

- sources searched;
- candidate byte-entry facts reviewed;
- accepted/parser-asserted decision or blocker reason;
- parser behavior before/after;
- tests proving fact-state correctness.

## Resolution

Decision: blocked/deferred, not accepted/parser-asserted.

Trace blocks:

- Sources searched: `Inside_Macintosh_Volume_II_1985.md` Segment Loader /
  Jump Table pages, `Programming_With_Macintosh_Programmers_Workshop_1987.md`
  object/link entry references, `MPW_and_Assembly_Language_Programming_for_the_Macintosh_1987.md`
  assembly/link tutorial context, and existing Mac KB packets/facts.
- Cited support found: nonzero CODE segment headers, CODE 0 jump-table/A5
  metadata, jump-table entry relationships, CODE 1 startup through the first
  jump-table entry, and MPW object main-entry context.
- Missing support: no cited or parser-asserted rule for the executable byte
  offset inside nonzero CODE payloads, no rule tying first jump-table routine
  entry semantics to that byte offset, and no source/object/link map that would
  let MPW object main-entry evidence authorize observed CODE resource bytes.
- Candidate facts reviewed: `macos.code_resource.movea_stack_a0.boundary` and
  `macos.code_resource.movea_stack_a0.entry_candidate` remain candidate-only.
- Deferred facts reviewed: `macos.code_resource.byte_entry_rule.unknown`
  remains deferred.
- Parser behavior before/after: unchanged. Parser output may emit the observed
  `movea.l (a7)+,a0` boundary only as candidate evidence and must keep missing
  byte-entry authority deferred.

Added blocker packet:

```text
macos.packet.byte_entry_rule.blocked
```

## Research Coverage

- [x] Local Mac docs searched for byte-entry evidence.
- [x] MPW docs searched for startup/segment entry evidence.
- [x] Existing byte-entry KB facts reviewed.
- [x] Project-observed MPW `Asm` byte patterns classified.
- [x] Migration-or-defer decision recorded.
- [x] Proposal 012/018 wording checked.

## Research Review

- [x] Second pass checked weak evidence is not promoted.
- [x] Candidate/deferred facts remain correctly labelled if no accepted rule is
  found.
- [x] Parser-output validation passes.
- [x] CODE 0 remains metadata-only.
- [x] Selected CODE 1 and preview behavior still works.
- [x] Proposal/docs updated with exact decision.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Byte-entry decision packet added.
- [x] KB facts updated or blocker explicitly recorded.
- [x] Parser behavior changed only if evidence supports it.
- [x] Candidate/deferred facts are not promoted without support.
- [x] Relevant parser/payload/artifact/web tests pass if behavior changes.
- [x] MPW `Asm` artifact regenerated if output changes.
- [x] `amiga_reversing.tools.platform_executable_formats validate` passes.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

```text
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m pytest tests\test_macos_asm_container.py tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py -q
19 passed
uv run python -m amiga_reversing.tools.validate_018_issues
```
