# PRD Notes

`docs/prd/` is for current implementation breakdowns derived from proposal
work. PRDs are planning artifacts, not durable architecture records.

Durable decisions belong in `docs/proposals/`. Ongoing top-level work can be
summarized in `TODO.md`.

## Naming

Keep the numbered filename style:

```text
023-short-topic.md
024-next-short-topic.md
```

Do not reuse numbers after deleting stale PRDs. Number gaps are useful history.

## Number Allocation

Last allocated PRD number: `022`.

The next PRD should normally use `023`, unless a newer PRD already exists.

When creating a new PRD, update this section in the same change. Issue parent
numbers follow PRD numbers, so this is also the source of truth for allocated
`docs/issues/` parent prefixes.

## Lifecycle

Delete PRDs when they are completed, abandoned, or superseded by a proposal,
newer PRD, issue set, or implemented code.

If a stale PRD still contains useful durable reasoning, promote that reasoning
into the relevant proposal before deleting the PRD.

Do not keep stale PRDs just to preserve numbering or historical planning text.

## Suggested Fields

New PRDs should usually include:

```text
Status:
Source proposal:
Created:
Supersedes:
Non-goals:
Acceptance criteria:
Deletion / cleanup expectations:
Verification:
Open questions:
```
