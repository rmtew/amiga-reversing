Status: Open
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Parse enough Rez/resource metadata to connect `Sample.r`, `Sample.h`,
`Sample.inc1.a`, and source call sites.

Initial resource types:

```text
MBAR
MENU
ALRT
DITL
WIND
RECT
SIZE
cmdo
```

Out of scope:
Do not implement full Rez syntax, full resource binary compilation, or resource
round-trip.

Files likely touched:
- new Rez/resource parser under `src/scripts/` or reusable platform module
- tests under `tests/`
- generated metadata only if needed by render tests

Acceptance criteria:
- `Sample.r` resources are inventoried with type, symbolic id, numeric id when
  resolvable, and attributes such as `preload` or `purgeable`.
- Constants from `Sample.h` and `Sample.inc1.a` resolve resource IDs used by
  both Rez and assembly.
- Source call sites connect `rWindow`, `rMenuBar`, `rStopRect`, `rGoRect`,
  `rAboutAlert`, and `rUserAlert` to resource declarations.
- `Count.r` `cmdo` is inventoried as MPW tool command metadata.

Required tests:
- `Sample.r` resource inventory test.
- `Sample.h` and `Sample.inc1.a` constant-resolution test.
- Resource-to-source xref test for `_GetNewWindow`, `_GetNewMBar`,
  `_GetResource`, and `_Alert`.
- `Count.r` `cmdo` smoke test.

Cleanup / deletion:
Delete after resource ID parsing is implemented and durable notes are promoted.

Notes for agents:
This is source/resource semantic parsing, not resource-fork binary parsing. Keep
it separate from the `Asm` `CODE` resource importer.
