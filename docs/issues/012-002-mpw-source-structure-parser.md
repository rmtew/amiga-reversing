Status: Open
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Parse enough MPW assembly source structure to render `Sample`, `Memory`, and
`Count` as Classic Mac OS source projects.

Required constructs:

```text
INCLUDE
IMPORT
EXPORT
SEG
MAIN
PROC / FUNC
ENDP / ENDF / ENDPROC / ENDF
RECORD / ENDR
WITH
```

Out of scope:
Do not implement a full MPW assembler, macro expander, object writer, or
round-trip build.

Files likely touched:
- new parser under `src/scripts/` or reusable platform module
- `knowledge/mac_os.json` only if needed for parser-owned facts
- tests under `tests/`

Acceptance criteria:
- Parser emits source files, includes, imports, exports, segments, routines,
  records, and basic line ranges for `Sample.a`, `SampleMisc.a`,
  `Sample.inc1.a`, `MemorySrc.a`, and `Count.a`.
- `SEG 'Initialize'` and `SEG 'Main'` are preserved as source segment facts.
- `MAIN` in `MemorySrc.a` is represented as a desk-accessory/source entry
  marker, not as an application `CODE 1 Main` claim.
- Source segment facts are explicitly distinct from observed linked `CODE`
  resource facts.

Required tests:
- Parser fixture tests for `Sample.a` and `SampleMisc.a`.
- Parser fixture test for `MemorySrc.a` `MAIN`.
- Regression test that source segment names are not mapped to `Asm` CODE
  resources by name alone.

Cleanup / deletion:
Delete after MPW source structure parsing is implemented and covered by tests.

Notes for agents:
Preserve MacRoman text handling. Do not "fix" MPW source encoding as part of
this parser unless a test proves the conversion is wrong.
