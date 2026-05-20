# Classic Mac OS File Structure Notes

Classic Mac OS files are not flat executable blobs in the Atari PRG or Amiga
HUNK sense. HFS gives a file both a data fork and a resource fork, and Inside
Macintosh describes application code itself as resources in the resource fork.

Relevant local citations:

- `ext/docs_macos/Inside_Macintosh_Volume_I_1985.md`, page 117: every file has
  data and resource forks; an application resource fork contains resources and
  application code; code may be split into resource segments.
- `ext/docs_macos/Inside_Macintosh_Volume_II_1985.md`, pages 69-71: the Segment
  Loader uses `CODE` resources, with `CODE` resource ID 0 holding the jump table
  and `CODE` resource ID 1 holding the main segment.

For MPW-GM, the HFS inventory shows the 68K assembler here:

```text
MPW-GM/MPW/Tools/Asm
type: MPST
creator: MPS
data fork: 10752 bytes
resource fork: 213850 bytes
```

Running the resource-fork inspector over the `Asm` resource fork finds 28
`CODE` resources totaling 206404 bytes. That means the useful 68K reference code
is in segmented `CODE` resources, not in the small data fork.

Generated metadata:

```text
ext/macos_tools/mpw_gm/source.json
ext/macos_tools/mpw_gm/asm_code_resources.json
```

Regeneration sketch:

```powershell
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'
uv run python src\scripts\extract_classic_hfs.py tmp\MPW-GM.ext-tool.raw `
  --extract tmp\mpw_asm_resource_probe `
  --path-prefix "MPW-GM/MPW/Tools/Asm" `
  --resource-forks

uv run python src\scripts\inspect_mac_resource_fork.py `
  tmp\mpw_asm_resource_probe\resource\MPW-GM\MPW\Tools\Asm `
  --type CODE `
  --output ext\macos_tools\mpw_gm\asm_code_resources.json
```

Next parser target:

```text
HFS catalog record -> data/resource forks -> resource map -> CODE resources
                                                     -> segment metadata
                                                     -> m68k disassembly input
```
