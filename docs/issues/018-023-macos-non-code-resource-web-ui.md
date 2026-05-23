# 018-023: Mac OS Non-CODE Resource Web UI

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS non-CODE resource metadata visibility
- Blocked by: `018-014`
- Work order: may run after `018-018`; avoid concurrent edits with `018-024`
  because both touch Mac web container UI.
- Current proposal state: non-CODE resource metadata inventory exists as
  candidate/deferred knowledge, and the artifact has placeholders, but the web
  UI does not present a useful non-CODE resource detail view.
- Desired proposal state after this issue: Mac web UI exposes non-CODE resource
  metadata inventory with candidate/deferred labels and CDP verification.

## Knowledge Delta

- Adds: browser-visible non-CODE resource metadata obligations.
- Changes: non-CODE resources become visible as structured metadata, not only
  count/placeholders.
- Replaces: raw resource type list as the only web-visible non-CODE surface.
- Deletes: no candidate/deferred state.
- Leaves out of scope: decoding resource payload semantics, accepting unknown
  resource formats, and CODE preview/listing changes.

## Default Behavior

- Non-CODE resource semantics remain candidate/deferred unless already accepted.
- UI must distinguish known metadata, candidate metadata, deferred, unsupported,
  and unknown.
- Do not imply non-CODE payload decoding is complete.
- CODE resource UI behavior must remain unchanged.

## Evidence Standard

- Browser-visible rows must show resource type/count/status and evidence reason
  or inventory source.
- CDP must verify at least one non-CODE metadata row and one candidate/deferred
  label.
- Tests must ensure CODE preview UI is not regressed.

## Implementation Slice

- Trace 018-014 inventory output and current Mac project payload fields.
- Add/extend payload only if needed to expose structured non-CODE metadata.
- Render non-CODE metadata in the Mac web container view.
- Add focused web/source tests and CDP verification.
- Update docs with current candidate/deferred non-CODE UI state.

## Research Completion Standard

Record trace blocks for:

- inventory source consumed;
- payload fields added or reused;
- UI shape selected;
- CDP assertions;
- non-goals for payload decoding.

## Research Notes

Trace blocks:

```text
Inventory source consumed:
  binary_container_view.resource_fork.types from the C-backed
  platform_file_lib.macos_hfs_code_summary output.

Payload fields added:
  binary_container_view.resource_fork.non_code_resource_details[] with
  resource_type, resource_count, kb_record_id, fact_id, fact_status,
  parser_use, payload_decode_status, inventory_source, and reason.

UI shape:
  The Mac container panel renders a separate Non-CODE Resource Metadata block
  before CODE Resource Details. Rows show type, count, candidate/parser-use
  state, unsupported payload decode status, and inventory evidence.

CDP assertions:
  The Mac project page must show Non-CODE Resource Metadata, a non-CODE type
  such as CURS, candidate/candidate_only state, unsupported decode status, and
  still show the existing CODE preview rows.

Non-goal:
  No non-CODE payload bytes are decoded and no non-CODE resource semantics are
  promoted to accepted output.
```

## Completion Evidence

```text
uv run python -m pytest tests\test_macos_project_payload.py tests\test_web_app_source.py -q
22 passed
node --check amiga_reversing\web\app.js
uv run python -m pytest tests\test_web_e2e_cdp.py::test_brave_cdp_macos_code_details_show_candidate_previews -q
1 passed
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.validate_018_issues
uv run ruff check amiga_reversing\disasm\macos_project_payload.py tests\test_macos_project_payload.py tests\test_web_app_source.py tests\test_web_e2e_cdp.py
All checks passed!
```

## Research Coverage

- [x] 018-014 inventory reviewed.
- [x] Current payload non-CODE fields traced.
- [x] UI shape selected.
- [x] CDP assertions selected.
- [x] CODE UI regression risk checked.
- [x] 012/018 wording checked.

## Research Review

- [x] Second pass checked non-CODE semantics are not over-accepted.
- [x] CODE preview/listing UI still works.
- [x] Candidate/deferred labels are visible.
- [x] CDP verifies browser-rendered non-CODE rows.
- [x] Proposal/docs updated.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Non-CODE metadata inventory visible in Mac web UI.
- [x] Candidate/deferred/unsupported labels preserved.
- [x] CODE resource UI behavior remains unchanged.
- [x] CDP browser verification passes.
- [x] Relevant web tests pass.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.
