Status: implemented
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

Review found the committed artifact is not yet that durable example. It
inventories all CODE resources but renders only `CODE 1`, and the rendered
listing begins by decoding Mac CODE metadata/data bytes as instructions through
the raw Amiga-style path. This issue remains open until the artifact demonstrates
starter-quality Mac rendering rather than a partial smoke test.

Rendering expectation:
`asm.s` should render the whole Mac executable file shape, not a standalone
`CODE 1` fragment:

```text
Finder type/creator and HFS path
data fork as preserved data/string payload or placeholder
resource fork summary
CODE 0 jump-table / Segment Loader metadata
all nonzero CODE resources as rendered ranges or named structured placeholders
classified code/data islands inside CODE resources
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
- `asm.s` must not emit Amiga-specific directives such as `SECTION code,code`.
- `asm.s` must not decode known or obvious CODE metadata/data bytes as bogus
  instructions. The initial `ori.b` metadata smell seen in the current artifact
  is a failing case, not acceptable starter output.
- Every CODE resource in the resource fork is accounted for as rendered
  Mac-style source or as a structured placeholder with a specific reason and
  next evidence needed.
- Obvious orphaned code islands are rendered when the entrypoint/control-flow
  evidence is available; otherwise they are explicitly recorded as deferred
  islands, not silently hidden inside data blobs.
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

Previous partial implementation:
- Added `targets/macos_hfs_mpw_gm/.project.json` as the committed Mac HFS
  container target for `resources/platform_macos/MPW-GM.img.bin`.
- Added `targets/macos_hfs_mpw_gm/targets/macos_file_mpw_tools_asm/.project.json`
  and `asm.s` for `MPW-GM/MPW/Tools/Asm`.
- `asm.s` is generated from the C-backed HFS/resource/CODE project path and the
  shared m68k listing renderer. It records Finder metadata, fork hashes,
  resource type counts, `CODE 0` Segment Loader metadata, all named CODE
  resources, non-CODE placeholders, unsupported loader/roundtrip scope, and real
  `CODE 1 Main` listing rows.
- Added `docs/macos-targets.md` to explain the committed target layout and
  regeneration policy.
- Added `tests/test_macos_target_artifact.py` for target loading, subtarget
  shape, and `asm.s` regeneration drift.

Review notes:
- The C-backed Mac summary now exposes resource type rows and CODE resource
  names/hashes so the committed artifact does not depend on the earlier
  Python-only prototype for visible executable/resource shape.
- Timestamp-only target state remains out of scope; the committed metadata uses
  stable origin/provenance fields and the generated `asm.s` carries the visible
  progress.

Corrective requirement:
- Regenerate and recommit `asm.s` only after 012-019 through 012-021 make the
  rendered source Mac-style, classify CODE layout correctly, and cover all CODE
  resources as rendered or explicitly deferred material.

Corrective closeout:
- 012-019 regenerated `asm.s` from the classified CODE 1 entrypoint, removing
  the bogus initial `ori.b` metadata decode.
- 012-020 regenerated `asm.s` through the Mac CODE listing adapter, removing
  the Amiga `SECTION code,code` directive from Mac-facing source.
- 012-021 added a drift-tested CODE resource coverage table so every CODE
  resource is represented as rendered, metadata-only, partial, or deferred with
  a concrete reason.
