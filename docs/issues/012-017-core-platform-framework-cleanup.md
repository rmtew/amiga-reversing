Status: Open
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Use Classic Mac OS support to cleanly extend the shared platform framework
rather than adding side paths.

Problem:
Classic Mac OS introduces source projects, fork/resource containers, and CODE
segment metadata that do not exactly match Amiga HUNK or Atari PRG. If the
current framework cannot express those concepts, the right fix is to generalize
the framework. A Mac-only workaround would create legacy code and tech debt.

Acceptance criteria:
- Any platform concept needed by Mac but also meaningful generally is represented
  in shared framework types or APIs.
- Mac-specific code is limited to actual Mac semantics: HFS/Finder metadata,
  resource fork/CODE conventions, MPW source/build semantics, and Mac OS facts.
- No compatibility branch exists only to preserve the prototype Python payload
  shape or helper API.
- If a clean framework extension is too large for the current slice, the blocker
  is recorded in this issue/proposal and implementation pauses at that boundary.
- Existing Amiga and Atari behavior remains supported through the generalized
  path, not through copied legacy branches.

Required tests:
- Shared project/source/container schema tests covering Amiga, Atari ST, and
  Classic Mac OS examples.
- Regression tests proving existing Amiga/Atari imports still use the shared
  framework path.
- Review checklist confirming no Mac-only workaround path remains.
