# 018-021: Mac OS Relocation/Fixup Citation Packet

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS Segment Loader relocation/fixup evidence
- Blocked by: `018-001`
- Work order: batch-safe with `018-022` and `018-025`; do not change parser,
  payload, artifact, or web behavior.
- Current proposal state: relocation/fixup interpretation is emitted as
  deferred-only. Proposal 012 remains blocked partly because relocation/fixup
  semantics are not accepted platform knowledge.
- Desired proposal state after this issue: local/allowed sources are reviewed
  and relocation/fixup claims are recorded as validated, parser-asserted,
  candidate, deferred, unsupported, or conflict evidence without changing
  runtime behavior.

## Knowledge Delta

- Adds: relocation/fixup citation packet and, where justified, KB fact records.
- Changes: relocation/fixup unknowns become source-backed accepted/candidate or
  explicitly deferred/conflict claims.
- Replaces: vague deferred relocation note as the only durable knowledge.
- Deletes: no existing deferred parser output.
- Leaves out of scope: parser implementation, preview/listing behavior,
  relocation application, roundtrip.

## Default Behavior

- Parser output remains unchanged unless a separate implementation issue opts in.
- Weak or ambiguous claims must stay candidate/deferred/conflict.
- Accepted facts require allowed old/out-of-print or compatible sources, or
  explicit parser assertions with reason and standard interpretation.
- Do not use incompatible modern sources.

## Evidence Standard

- Every claim must cite source path/page or state why it is parser-asserted.
- The packet must distinguish resource relocation, segment loading, jump-table
  fixups, A5 world assumptions, and unknowns.
- It must be clear which facts can later authorize parser output and which
  cannot.

## Implementation Slice

- Search local Mac docs/markdown and MPW materials for relocation/fixup
  evidence.
- Update `knowledge/platform_executable_formats.json` with citation packets or
  candidate/deferred records as justified.
- Update `docs/platform-executable-formats.md` and Proposal 018 notes.
- Add or extend KB validation tests if new fact states are introduced.
- Do not touch Mac parser/payload/web files.

## Research Completion Standard

Record trace blocks for:

- sources searched;
- accepted evidence found;
- ambiguous/conflicting evidence;
- facts added and their status;
- parser behavior explicitly left unchanged.

## Research Coverage

- [x] Local Mac docs searched.
- [x] MPW docs searched.
- [x] Existing KB relocation facts reviewed.
- [x] Accepted/candidate/deferred/conflict claims selected.
- [x] Parser behavior non-change checked.
- [x] Source policy checked.

## Research Review

- [x] Second pass checked every accepted fact has citation/assertion support.
- [x] Weak claims are not accepted.
- [x] Incompatible sources are not used.
- [x] Parser/payload/web files are not modified.
- [x] Proposal/docs updated with exact status.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Relocation/fixup citation packet or deferred packet added.
- [x] Fact statuses match evidence strength.
- [x] Parser behavior remains unchanged.
- [x] Source policy recorded.
- [x] `amiga_reversing.tools.platform_executable_formats validate` passes.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

- Searched local Inside Macintosh and MPW markdown for Segment Loader,
  relocation, fixup, A5, and jump-table evidence.
- Updated `macos.packet.segment_relocation_fixups.deferred` to record the
  stronger 018-021 result: local sources support Segment Loader memory
  relocation context but not accepted CODE fixup byte layout.
- Added candidate packet
  `macos.packet.segment_loader.memory_relocation_context`.
- Preserved `macos.segment_loader.relocation_fixups.deferred` as
  deferred-only; no parser/payload/artifact/web behavior changed.
- Updated `docs/platform-executable-formats.md` and Proposal 018 notes.
- Validation run:
  `uv run python -m amiga_reversing.tools.platform_executable_formats validate`
- Issue validation run:
  `uv run python -m amiga_reversing.tools.validate_018_issues`
