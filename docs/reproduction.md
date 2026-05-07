# Reproduction Workflow

The web UI reproduction pass re-renders source from the current target analysis,
assembles it, and byte-diffs the rebuilt binary against the original. The source
listing is ephemeral; durable user intent belongs in target metadata.

## Exactness Gate

Reproduction uses `facts_v2` analysis with direct platform rebuild. There is no
selectable analysis path in the Python UI, CLI, benchmark, or reproduction paths.

The primary exactness gate is our assembler/direct object rebuild path:

```text
m68k_assembler_app.exe assemble-platform-file --cpu <cpu> --backend <backend> source.s rebuilt.bin
```

The backend is resolved from the binary source:

```text
amiga-hunk   Amiga HUNK files and Amiga disk entries
atari-st     Atari ST .PRG, .TOS, .TTP, and ST/MSA disk entries
amiga-raw    raw binary targets; currently reported unsupported for exact repro
```

`vasm` and DevPac should remain oracle modes for compatibility/file-shape
questions. They are not the web UI exactness gate.

For `facts_v2`, reproduction correctness is structural first. Direct rebuild
bytes are the gating artifact; source rendering is a separate readiness check.
When source cannot be rendered safely, the profile records refusal counters
instead of emitting degraded symbolic/numeric output.

## facts_v2 Gates

Run the gates that cover the active default path:

```powershell
$env:AMIGA_REVERSING_FULL_REPRO_INTEGRATION='1'
$env:AMIGA_REVERSING_FULL_REPRO_PROFILE='1'
$env:AMIGA_REVERSING_FULL_REPRO_REPORT='bin\rebuilt\full_reproduction_report_default_facts_v2.json'
python -m pytest tests\test_full_reproduction_integration.py -q
```

```powershell
$env:AMIGA_REVERSING_FULL_REPRO_INTEGRATION='1'
$env:AMIGA_REVERSING_FULL_REPRO_FACTS_V2_SOURCE_GATE='1'
$env:AMIGA_REVERSING_FULL_REPRO_PROFILE='1'
$env:AMIGA_REVERSING_FULL_REPRO_REPORT='bin\rebuilt\full_reproduction_report_facts_v2_source_gate.json'
python -m pytest tests\test_full_reproduction_integration.py -q
```

The facts_v2 state is ready only when the report's `facts_v2_readiness`
object has `facts_v2_reproduction_default_ready: true`,
`source_render_default_ready: true`, and empty `blockers`,
`direct_rebuild_blockers`, and `source_render_default_blockers`.

The source gate compares source-assembled output by payload and relocation
semantics. Byte differences from canonical relocation ordering are reported but
do not block source readiness.

`amiga-precommit` runs these facts_v2 gates by default. To skip them during a
local fast edit loop, opt out explicitly:

```powershell
$env:AMIGA_REVERSING_PRECOMMIT_FACTS_V2_GATE='0'
uv run amiga-precommit
```

Precommit benchmarks the normal `facts_v2` path.

## Current Stamp Inputs

`reproduction.json` is fresh only when its input stamp matches the current
project. The stamp includes:

```text
original binary sha256 and size
effective metadata sha256
renderer id and tool stamps
platform_file_lib.dll and platform_disk_lib.dll stamps
assembler path and file stamp
backend
reproduction options
```

If any stamp input changes, the UI should display the reproduction result as
stale and rerun it after full listing analysis is ready.

## Target Metadata Inputs

Analysis-affecting edits must be represented as structured target metadata, not
edited source. The effective metadata merge order is:

```text
target_metadata.json
target_seeded_metadata.json
target_corrections.json
UI-created target edits
```

Use metadata for code/data ranges, entrypoints, labels, pointer tables, text
ranges, jump tables, external symbols, and suppressions. Keep display-only notes
in `overrides.json`.

## Assembler Repro Options

These options are read per target from `reproduction` objects in
`target_metadata.json`, `target_seeded_metadata.json`, `target_corrections.json`,
and UI edit records with kind `reproduction_options`. Later files/edits override
earlier ones.

```json
{
  "reproduction": {
    "mode": "exact",
    "assembler": "our",
    "cpu": "any",
    "backend": "auto",
    "include_dirs": "auto",
    "oracle_modes": [],
    "container_policy": "preserve_original",
    "relocation_policy": "preserve_original_encoding",
    "comparison": "full_file",
    "file_shape": {
      "relocation_order": "match_original",
      "relocation_record": "auto",
      "section_aux_order": "assembler-default"
    },
    "raw_output": null
  }
}
```

`assembler` selects the exactness assembler. Today only `our` is supported for
the gate; any other value is reported as a tooling error rather than silently
ignored.

`cpu` selects the M68K ISA level passed to the assembler. The default is `any`,
which accepts every KB-defined form for byte reproduction while the original CPU
policy is not known. Set this per target only when the target must reject later
ISA forms during reproduction.

`backend` may stay `auto` unless a target needs an explicit `amiga-hunk`,
`atari-st`, or future raw backend.

`include_dirs` defaults from the backend. List values are stamped for
target-specific include sets or fixture isolation; backend auto-includes remain
the only directories passed to the current exactness command.

`oracle_modes` records requested extra non-gating checks such as `vasm` or
`devpac`. Oracle execution is still future work and must be reported separately
from exact byte reproduction when added.

`mode` is a convenience layer over the lower-level policies:

```text
exact                full file comparison with configured shape preservation
template_preserved   preserve original container shape, payloads come from rebuild
canonical            compare the assembler's default output shape
content              allow payload/relocation content match without file exactness
semantic             reserved for richer semantic equivalence; currently content-level
```

`container_policy` controls non-payload file shape. `preserve_original` uses the
original container as a template where this is safe. For Amiga HUNK files this is
only applied when rebuilt relocation semantics match the original, so original
relocation records cannot mask a bad rebuild.

`relocation_policy` controls relocation encoding. `preserve_original_encoding`
allows shape-preserving rewrites such as Amiga relocation offset/group ordering
when the relocation set is otherwise equivalent.

`comparison` controls the selected result layer. `full_file` requires byte exact
output. `content` reports a `content_match` status when payload bytes and
relocation semantics match but the container still differs.

`file_shape.relocation_order` supports `assembler-default` and, for Amiga HUNK
targets, `match_original`. `match_original` keeps the assembler's relocations
only when the rebuilt relocation groups contain the same target sections and
offset sets as the original, then rewrites the rebuilt relocation offset order to
the original file shape. Use it for targets where payload bytes match but the
original linker emitted relocation offsets in a non-default order.

`file_shape.relocation_record` and `file_shape.section_aux_order` are reserved
for future target-specific output-container policy. These settings should not
change the disassembled source semantics.

`raw_output` is reserved for raw binary targets once the assembler has a raw
writer mode.

## Section Allocation Labels

Disassembly source should represent the original section allocation, not only
the stored payload bytes. If a file format section allocates more bytes than it
stores, render the payload normally, then render the allocation-only tail with
`DS.B` and a comment such as:

```asm
    ; reserved allocation tail: payload ends at $118, section allocates $384
h2_0118:
    DS.B    $26C
```

Relocations or metadata labels that target the allocation tail, or the exact end
of a stored section, must get real labels at their target offsets. Do not encode
these as a base label plus offset merely because the target has no payload byte.

This is not target-specific casing. It is the source-level representation needed
for exact object layout. Target-specific reproduction options should only choose
container, relocation, and comparison policies when the original linker/compiler
file shape differs from the assembler default.

## Symbolic Operands

Source should keep useful symbolic operands such as `LN_SUCC(a1)`. Exactness is
the assembler's responsibility: if a symbol resolves to zero in an address
register displacement, the assembler may encode the shorter `(aN)` form while
preserving the symbol in rendered source and UI context.
