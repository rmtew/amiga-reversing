# 0001-012 Reject Reserved Manual Action Fields

## Parent

PRD 0001: Manual Review Workflow

## What to build

Validate Manual Action Log appends so caller-provided action payloads cannot override reserved log fields. Action identity, sequence, timestamp, record type, and action kind must be owned by the append path, not by UI or API payload data.

This protects replay order and log integrity without changing the public manual action concepts.

## Acceptance criteria

- [ ] Manual action append rejects payloads containing reserved fields such as record type, action id, sequence, timestamp, or kind.
- [ ] API requests cannot override generated Manual Action Log identity or ordering fields.
- [ ] Valid action payloads continue to append with generated id, next sequence, timestamp, and requested kind.
- [ ] Invalid append attempts return a clear client-facing error and do not write partial log records.
- [ ] Tests cover direct projection/appending and the web API path.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

- 0001-001 Manual Action Log Projection

