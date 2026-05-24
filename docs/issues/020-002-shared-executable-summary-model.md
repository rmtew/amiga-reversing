# 020-002: Shared Executable Summary Model

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: 020-001.
- Current state: parser inspect summaries emit platform facts, but there is no
  shared C-owned executable range model consumed by later import/listing work.
- Desired state after this issue: the first shared executable summary/range
  model exists and the current synthetic Amiga HUNK parser fixture emits it
  with tests. This issue does not migrate listing, analysis import, Atari, or
  Mac CODE behavior.

## What To Build

Implement the initial shared C-owned executable summary/range model. Use the
current Amiga HUNK synthetic fixture as the first proof because it already runs
through `platform_file_inspect_path_json_alloc`, has CODE/DATA/BSS sections,
and avoids the higher-risk Mac `RawBinarySource` bridge.

Expose the model through raw parser inspect JSON as a new shared range list
such as `executable_ranges`. Keep the existing `sections` and `fact_refs`
surfaces intact for now so 019 coverage stays green. Later issues will migrate
Atari, Mac, listing/rendering, and analysis import.

Minimum range fields:

```json
{
  "role": "code",
  "status": "parser_asserted",
  "parser_use": "accepted_parser_output",
  "fact_id": "amiga.hunk.code_data_bss.sections.accepted",
  "source_offset": 0,
  "size": 4,
  "stored_size": 4
}
```

The exact field names may differ if the C code already has a better local
convention, but the output must carry role, byte span, stored size, fact id,
fact status, and parser-use authority.

## Acceptance Criteria

- [ ] Shared C data shape exists for executable summary/ranges.
- [ ] Raw Amiga HUNK parser inspect JSON exposes shared ranges for the current
  synthetic HUNK fixture.
- [ ] Shared ranges include CODE, DATA, and size-only BSS representation.
- [ ] Shared range output includes KB record/fact refs and fact states.
- [ ] Runtime-entry or relocation-breadth uncertainty is represented as a
  non-accepted/deferred marker where the current 018/019 facts require it.
- [ ] Tests validate raw summary output before Python coverage wrapping.
- [ ] Current `coverage --current-amiga-hunk` behavior still passes from the
  existing parser-owned refs.
- [ ] No listing, analysis-state import, Atari PRG, or Mac CODE migration is
  performed in this issue.
- [ ] Proposal 020 records the chosen first fixture and any model constraints.

## Blocked By

- 020-001

## Required Sign-Off

- [ ] No Python-only durable model.
- [ ] No legacy compatibility path.
- [ ] Existing `sections`/`fact_refs` inspect output is not broken.
- [ ] Candidate/deferred/unsupported states remain non-accepted.
- [ ] `platform_executable_formats validate` passes.
- [ ] Combined current coverage still passes.
- [ ] Focused tests for the touched parser path pass.
- [ ] `git diff --check` passes.

## Completion Evidence

Record the raw Amiga parser summary shape, the focused tests, any naming/model
constraints discovered, and whether 020-003 or 020-004 should use the model
next.
