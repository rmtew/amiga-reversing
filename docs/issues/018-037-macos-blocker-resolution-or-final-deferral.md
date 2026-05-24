# 018-037: MacOS Blocker Resolution or Final Deferral

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Blocked by: `docs/issues/018-036-macos-executable-kb-closeout-research.md`
- Purpose: convert the 018-036 research packets into durable executable-format
  KB state, either by accepting/parser-asserting facts or by formally deferring
  unsupported facts with downstream blocker semantics.

## Knowledge Delta

For each Mac blocker from 018-036:

- add accepted or parser-asserted KB facts only when the research packet meets
  the evidence standard;
- otherwise add or update candidate/deferred/unsupported records that explain
  the missing evidence and required downstream behavior;
- ensure byte-entry and relocation/fixup states cannot be mistaken for accepted
  parser authority if they remain unresolved.

The expected useful outcome may be a formal deferral, not an implementation.

Completed 018-037 result:

| 018-036 blocker | KB state after this issue | Parser/report behavior |
| --- | --- | --- |
| Nonzero CODE byte-entry rule / `movea.l (a7)+,a0` | `macos.code_resource.byte_entry_rule.unknown` remains `deferred` with `final_resolution=formal_deferred`; `macos.code_resource.movea_stack_a0.boundary.candidate` remains `candidate_only`. | Unchanged. Accepted closeout remains blocked until a cited or parser-asserted byte-entry rule exists and parser output validates against it. |
| Classic 68K CODE relocation/fixup record format | `macos.segment_loader.relocation_fixups.deferred` records the missing on-disk record location, byte encoding, affected payload offsets, Segment Loader application rules, and relocated-byte fixture. | Unchanged. Parser/report output may emit placeholders only; no accepted relocation interpretation is authorized. |
| Source-to-CODE fixture proof | `macos.source_to_code.fixture_product.deferred` records that a candidate source fixture's own built product must be captured or reproduced before source-to-CODE mapping. | Unchanged. Current Sample source must not be mapped to MPW/Tools/Asm CODE resources. |
| Non-CODE resource payload semantics | `macos.resource_fork.curs.layout.accepted` remains type-level accepted; `macos.resource_fork.curs.payload_decode.unsupported` records payload decoding as unsupported; `acur`, `cmdo`, and `vers` remain candidate inventory. | Unchanged. Resource rows may expose accepted type-level CURS semantics only, not decoded payload fields. |

## Default Behavior

Default parser/listing/web behavior changes only when backed by accepted or
parser-asserted KB state. If facts remain deferred, current candidate visibility
may remain but accepted parser behavior must not broaden.

## Evidence Standard

All KB state changes must trace directly to 018-036 evidence packets. No
standalone promotion is allowed in this issue.

## Implementation Slice

AFK implementation/docs slice:

- update `knowledge/platform_executable_formats.json` with the resolved Mac
  fact states;
- update validation tests so accepted/candidate/deferred/unsupported boundaries
  are enforced;
- update parser/report surfaces only if needed to consume or expose the resolved
  state accurately;
- update Proposal 018 and Proposal 012 closeout notes with the downstream
  meaning.

## Research Completion Standard

This issue inherits the 018-036 research. It is complete only when every 018-036
blocker has a durable KB state and downstream parser behavior is either updated
or explicitly unchanged for a recorded reason.

## Research Coverage

- [x] 018-036 evidence packets checked before edits.
- [x] KB state updated or explicitly confirmed for every Mac blocker.
- [x] Parser-use authority reviewed for every changed fact.
- [x] Proposal 012 downstream blocker wording reviewed.
- [x] Second-pass review checked for accidental candidate-to-accepted leakage.

## Research Review

- [x] Byte-entry status is accepted/parser-asserted only with evidence, otherwise
  formally deferred.
- [x] Relocation/fixup status is accepted/parser-asserted only with evidence,
  otherwise formally deferred.
- [x] Source-to-CODE fixture state is recorded without mixing MPW/Tools/Asm with
  unrelated source examples.
- [x] Non-CODE payload semantics do not broaden beyond cited facts.
- [x] Tests enforce the resulting fact-state boundaries.

## Required Sign-Off

- [x] Platform executable KB validation passes.
- [x] Platform executable format tests pass.
- [x] Relevant Mac parser/listing tests pass if parser/report files changed.
- [x] Proposal 018 and Proposal 012 record the final downstream state.

## Completion Evidence

- `uv run python -m amiga_reversing.tools.platform_executable_formats validate`
  passed.
- `uv run python src/scripts/generate_platform_format_runtime.py` refreshed the
  generated fact table from `knowledge/platform_executable_formats.json`.
- `uv run python -m pytest tests/test_platform_executable_formats.py -q`
  passed.
- `uv run python -m pytest tests/test_validate_018_issues.py -q` passed.
- `git diff --check` reported only existing CRLF whitespace warnings and no
  new whitespace errors.
