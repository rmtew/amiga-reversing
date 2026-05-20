Status: implemented; superseded by open completion issues
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Remove stale unchecked-task markers from Proposal 012 after the starter
milestone closeout.

Problem:
The proposal status now says the starter milestone is implemented with future
work deferred, but the "Checkpoint Index" still used unchecked task boxes for
every section. That made the proposal look unstarted even though the current
implementation and tests cover the starter milestone.

Acceptance:
- The index no longer looks like a stale open task list.
- Deferred future work remains explicit.
- Completed issue files are intentionally retained because the active thread
  objective still uses `docs/issues/012-*` as the working issue record.

Result:
- The proposal now uses a neutral section index and documents that issue-file
  deletion is deferred until after this active objective no longer needs the
  per-issue evidence trail.

Superseding note:
The neutral index remains valid, but the proposal is not closed. Open completion
issues now define the remaining work needed for full Classic Mac OS platform
support without legacy paths or prototype-only compatibility shims.
