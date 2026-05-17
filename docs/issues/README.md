# Issue Notes

`docs/issues/` is for current executable slices derived from proposals.
Issue files are working plans, not a permanent issue tracker.

Durable decisions belong in `docs/proposals/`. Broad remaining work can be
summarized in `TODO.md`.

## Naming

Keep the proposal-number plus slice-number filename style:

```text
004-001-first-slice.md
004-002-second-slice.md
008-001-next-proposal-first-slice.md
```

The first number must match the source proposal number. The second number is the
slice number within that proposal. Do not use a separate parent-number
allocator.

## Lifecycle

Delete issue files when they are completed, abandoned, or superseded.

If a stale issue still contains useful durable reasoning, promote that reasoning
into the relevant proposal before deleting the issue.

Do not keep stale issue files just to preserve numbering or historical planning
text.

## Suggested Fields

New issue files should usually include:

```text
Status:
Source proposal:
Scope:
Out of scope:
Files likely touched:
Acceptance criteria:
Required tests:
Cleanup / deletion:
Notes for agents:
```
