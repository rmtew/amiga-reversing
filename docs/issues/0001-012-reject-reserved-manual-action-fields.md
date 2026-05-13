# 0001-012 Reject Reserved Manual Action Fields

## Parent

PRD 0001: Manual Review Workflow

## What to build

Validate Manual Action Log appends so caller-provided action payloads cannot override reserved log fields. Action identity, sequence, timestamp, record type, and action kind must be owned by the append path, not by UI or API payload data.

This protects replay order and log integrity without changing the public manual action concepts.

## Acceptance criteria

- [x] Manual action append rejects payloads containing reserved fields such as record type, action id, sequence, timestamp, or kind.
- [x] API requests cannot override generated Manual Action Log identity or ordering fields.
- [x] Valid action payloads continue to append with generated id, next sequence, timestamp, and requested kind.
- [x] Invalid append attempts return a clear client-facing error and do not write partial log records.
- [x] Tests cover direct projection/appending and the web API path.
- [x] CDP tests pass.
- [x] `cmd /c src\precommit.bat` passes.

## Completed

- Manual action appends now reject reserved top-level payload fields before opening or writing a log.
- The manual-action HTTP route validates payloads before calling the append path.
- Tests cover direct append rejection and API route rejection.

## Verification

- `uv run python -m pytest tests\test_manual_action_log.py::test_append_manual_action_rejects_reserved_payload_fields tests\test_disasm_server.py::test_manual_action_route_rejects_reserved_payload_fields -q`
- `uv run ruff check amiga_reversing\disasm\manual_actions.py amiga_reversing\disasm\server.py tests\test_manual_action_log.py tests\test_disasm_server.py`
- `M68K_RUN_BRAVE_CDP=1 uv run python -m pytest tests\test_web_e2e_cdp.py -q`
- `cmd /c src\precommit.bat`

## Blocked by

- 0001-001 Manual Action Log Projection
