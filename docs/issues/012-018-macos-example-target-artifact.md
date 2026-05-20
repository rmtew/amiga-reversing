Status: blocked
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Commit an illustrative, evolving Mac OS target/subtarget under `targets/` that
shows visible progress as platform support improves.

Required shape:

```text
targets/macos_hfs_mpw_gm/
  .project.json
  manifest / container metadata as appropriate
  targets/macos_file_mpw_tools_asm/
    .project.json
    asm.s
    structured manual/progress facts when supported
```

The container target represents `resources/platform_macos/MPW-GM.img.bin`.
The `macos_file_mpw_tools_asm` subtarget represents the HFS file
`MPW-GM/MPW/Tools/Asm`.

Problem:
The current Mac OS work proves parsing and rendering internally, but it does not
leave a committed target artifact that outside readers can inspect. The project
should have a visible Mac OS example like the existing Amiga targets: a durable
rendered `.s` file plus structured target/manual facts that demonstrate why the
platform work is useful.

Rendering expectation:
`asm.s` should render the whole Mac executable file shape, not a standalone
`CODE 1` fragment:

```text
Finder type/creator and HFS path
data fork as preserved data/string payload or placeholder
resource fork summary
CODE 0 jump-table / Segment Loader metadata
CODE 1 Main listing rows when supported
other CODE resources as named segments/placeholders until imported
non-CODE resources as structured placeholders/references
explicit unsupported state for relocation/fixups/complete Segment Loader behavior
```

The output should aim to read like a period-authentic Mac OS assembly project
where practical, but it has no byte-for-byte roundtrip contract. Placeholders
and external resource references are acceptable when they make the executable
shape clear.

Out of scope:
Do not commit a target generated only by the current Python prototype. This issue
depends on the C-backed Mac container/project path. Do not require MPW
Asm/Link/Rez roundtrip.

Acceptance criteria:
- The committed container target is named `macos_hfs_mpw_gm`.
- The committed `Asm` subtarget is named `macos_file_mpw_tools_asm`.
- The subtarget commits `asm.s`, not a noisy target-id-prefixed source filename.
- `asm.s` includes provenance to the source image, HFS path, fork, resource
  type/id/name, and selected CODE segment metadata.
- `asm.s` renders the whole Mac file/executable shape with real listing rows
  for imported CODE segment(s) and structured placeholders for unsupported or
  not-yet-imported parts.
- Structured manual/progress facts may be committed when they demonstrate
  meaningful Mac semantic progress; timestamp-only or cosmetic state is not
  accepted as progress.
- `docs/macos-targets.md` explains the target layout, how to read the committed
  `.s`, what manual/progress facts mean, and which unsupported areas remain.
- A regeneration/drift check fails when the committed `asm.s` no longer matches
  the current renderer output.

Required tests:
- Target creation/import test for `targets/macos_hfs_mpw_gm`.
- Subtarget render test for
  `targets/macos_hfs_mpw_gm/targets/macos_file_mpw_tools_asm/asm.s`.
- Drift check for the committed `asm.s`.
- Regression check that existing Amiga/Atari target rendering still uses the
  shared framework path.

Blocker recorded:
- Do not commit a Mac target generated only by the current Python prototype.
- The example target remains blocked until the C-backed Mac container/project
  path can generate a normal target/subtarget and the shared listing framework
  can render selected CODE resources as real m68k rows.
- Timestamp-only or helper-only target state is not accepted as 012 progress.
