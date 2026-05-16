# Issue Notes

`docs/issues/` is for current executable slices derived from PRDs or proposals.
Issue files are working plans, not a permanent issue tracker.

Durable decisions belong in `docs/proposals/`. Broad remaining work can be
summarized in `TODO.md`.

## Naming

Keep the parent-number plus issue-number filename style:

```text
023-001-first-slice.md
023-002-second-slice.md
024-001-next-topic-first-slice.md
```

Do not reuse parent numbers or issue numbers after deleting stale issue files.
Number gaps are acceptable and preserve history.

Parent-number allocation is tracked in `docs/prd/README.md`. Do not duplicate it
here.

## Lifecycle

Delete issue files when they are completed, abandoned, or superseded.

If a stale issue still contains useful durable reasoning, promote that reasoning
into the relevant proposal or PRD before deleting the issue.

Do not keep stale issue files just to preserve numbering or historical planning
text.

## Suggested Fields

New issue files should usually include:

```text
Status:
Parent PRD or proposal:
Scope:
Out of scope:
Files likely touched:
Acceptance criteria:
Required tests:
Cleanup / deletion:
Notes for agents:
```
