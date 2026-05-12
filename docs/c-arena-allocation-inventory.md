# C Arena Allocation Inventory

Scan scope: tracked files under `src`.

Scan command:

```powershell
git ls-files src | ForEach-Object { Select-String -Path $_ -Pattern '\b(malloc|calloc|realloc|free|arena_create)\s*\(' }
```

Categories: `workflow`, `result`, `caller_freed_output`, `external_read_buffer`, `test_only`, `keep_heap_for_now`.

## First Guard Candidates

- `src/m68k_source_model.c`: first raw-allocation guard target after migration to explicit **Result Arena**.
- `src/m68k_source_data.c`, `src/m68k_source_file_parse.c`, `src/m68k_source_file_emit.c`: next guard targets after their data buffers move to result/output ownership.
- `src/m68k_ir.c`: guard after IR result arena ownership is made explicit.

## Inventory

| File | Lines | Classification | Notes |
| --- | --- | --- | --- |
| `src/json_builder.c` | 26 | result | JSON builder arena. |
| `src/json_builder.c` | 95, 101, 107, 110, 186 | caller_freed_output | Returned JSON/text copy; keep heap until output API changes. |
| `src/m68k_analysis_facts_v2.c` | 340 | workflow | Facts pass workflow arena; work queues, maps, lookups, runtime ranges, and accepted-index scratch marks allocate from it. |
| `src/m68k_analysis_facts_v2.c` | 9166 | caller_freed_output | Facts text free API. |
| `src/m68k_analysis_render_lookup.c` | 3225, 9869 | workflow | Render lookup workflow arenas. Typed-flow graphs/queues and global-base observations are arena-backed; nested queues use scratch rewinds. |
| `src/m68k_assembler_app.c` | 107, 115 | external_read_buffer | Input file read buffer. |
| `src/m68k_assembler_app.c` | 373, 530, 551 | caller_freed_output | Assembled section data returned through app edge. |
| `src/m68k_assembler_app.c` | 593, 597 | caller_freed_output | Rendered text release at app edge. |
| `src/m68k_decode_ir.c` | 283 | result | Decode IR result arena. Section, candidate, and absent CPU arrays are arena-backed. |
| `src/m68k_fact_ir.c` | 25 | result | Facts IR result arena. Fact append storage is arena-backed. |
| `src/m68k_ir.c` | 291, 305 | result | Source file/source analysis own result arenas; section/section analysis receive explicit result arenas from callers. |
| `src/m68k_object.c` | 25 | result | Object arena. |
| `src/m68k_render_ir.c` | 191, 203, 3989 | result | Preview/lookup arenas. |
| `src/m68k_render_ir.c` | 314, 8807 | caller_freed_output | Preview source text. |
| `src/m68k_render_plan.c` | 15 | result | Render plan arena. |
| `src/m68k_render_plan.c` | 81, 163, 400, 419, 464, 638 | caller_freed_output | Text builder/output buffers. |
| `src/m68k_reproduction_compare.c` | 497, 522, 526 | workflow | Temporary fixup-match bitmap. |
| `src/m68k_source_data.c` | 15, 35, 39, 45, 49, 50, 53, 55, 71, 76, 81, 86, 91, 92, 96, 97 | workflow | Temporary parse buffers; source model copies data item bytes into its result arena. |
| `src/m68k_source_file_emit.c` | 144, 347 | workflow | Source file emit workflow arenas. Layout offsets and section writer slots are arena-backed; intermediate writer output flattens into destination arenas. |
| `src/m68k_source_file_parse.c` | 177, 183, 682, 687, 701, 706, 720, 725, 739, 744 | workflow | Temporary hex-blob buffers; Atari ST metadata chunks are copied into the source result arena. |
| `src/m68k_source_ir_api.c` | 52 | caller_freed_output | Public text free API. |
| `src/m68k_source_ir_render.c` | 1015 | workflow | Source render workflow arena. Label indexes, section label counts, and include cache storage are arena-backed. |
| `src/m68k_source_model.c` | 146 | result | Source model result arena creation. Append storage is arena-backed. |
| `src/platform_amiga_disk.c` | 1035 | result | Disk analysis arena. |
| `src/platform_amiga_disk.c` | 1219, 1228, 1233 | external_read_buffer | Disk image file read buffer. |
| `src/platform_amiga_hunk.c` | 84, 87, 94, 96, 103, 389, 394, 398, 412, 419, 424, 428, 526, 529, 542, 547, 557, 563, 567, 573, 582, 586, 593, 596, 687, 690, 698, 707, 747, 748, 749, 793, 794, 795, 799, 800, 801, 828, 835, 841, 845, 854, 857, 861, 865 | workflow | Hunk parser temporary names, arrays, section/debug buffers. |
| `src/platform_amiga_hunk.c` | 922, 929, 936 | external_read_buffer | Hunk file read buffer. |
| `src/platform_amiga_hunk.c` | 1449, 1455, 1460 | caller_freed_output | Writer output data. |
| `src/platform_atari_st.c` | 291, 309, 326, 327, 772, 773, 778, 779, 807, 813, 818 | caller_freed_output | Split payloads and writer output. |
| `src/platform_atari_st.c` | 367, 375, 383, 394, 400, 408, 414, 419, 424 | workflow | Relocation offset scratch. |
| `src/platform_atari_st.c` | 585, 592, 599 | external_read_buffer | Atari ST file read buffer. |
| `src/platform_atari_st_disk.c` | 178, 181, 183, 190, 196, 288, 291 | workflow | Cluster/subdirectory scratch. |
| `src/platform_atari_st_disk.c` | 300 | result | Disk analysis arena. |
| `src/platform_atari_st_disk.c` | 426, 435, 440 | external_read_buffer | Disk image file read buffer. |
| `src/platform_binary_io.c` | 23 | result | Binary writer arena. |
| `src/platform_binary_io.c` | 171 | caller_freed_output | Writer output bytes. |
| `src/platform_common.c` | 16, 26 | caller_freed_output | Path/string copies returned to caller. |
| `src/platform_disk_lib.c` | 83, 101, 1392, 1396 | caller_freed_output | Library text/data outputs. |
| `src/platform_disk_lib.c` | 140, 149 | external_read_buffer | Disk image read buffer. |
| `src/platform_disk_lib.c` | 173, 179, 573, 583, 634, 644 | caller_freed_output | Extracted file bytes. |
| `src/platform_disk_lib.c` | 479, 513, 540, 543, 1288, 1294, 1298, 1361 | workflow | Temporary payload/image ownership inside disk workflows. |
| `src/platform_file_amiga.c` | 3908, 3990, 4010, 4035 | workflow | Local workflow arenas. |
| `src/platform_file_amiga.c` | 3913, 3921, 4111, 4112, 4113, 4114, 4115, 4119, 4120, 4121, 4122, 4123, 4139, 4140, 4141, 4142, 4143 | workflow | Temporary analysis/cache workspaces. |
| `src/platform_file_cli.c` | 402 | workflow | CLI analysis policy scratch. |
| `src/platform_file_core.c` | 1451 | workflow | Core workflow arena. |
| `src/platform_file_decompression.c` | 873 | caller_freed_output | Decompression text output cleanup. |
| `src/platform_file_json.c` | 4384, 6213, 6706, 6755 | result | JSON result/index arenas. |
| `src/platform_file_lib.c` | 58 | caller_freed_output | String copy returned/stored for artifact. |
| `src/platform_file_lib.c` | 218, 220, 231, 4173, 4178, 4183, 4186, 4204, 4901, 4904, 4936, 4964, 4972, 4984, 4990, 4995, 6335, 6344, 6370, 6379, 6416, 6417, 7654, 7780, 7781, 7783 | caller_freed_output | Text/byte/JSON/artifact edge buffers and free APIs. |
| `src/platform_file_lib.c` | 4239, 4245, 5206, 5388, 5404, 6863, 6912, 7032, 7182, 7869, 7990 | workflow | Platform file workflow scratch arenas/buffers; facts/direct/reproduction policy/object workflows share `PlatformFileWorkflow`. |
| `src/platform_file_lib.c` | 5445, 5453 | external_read_buffer | Platform file read buffer. |
| `src/platform_file_lib.c` | 6758, 6771 | result | Listing artifact and listing index arena. |
| `src/test_m68k_container_metadata.c` | 192, 526 | test_only | Test output cleanup. |
| `src/test_m68k_ir.c` | 63, 77, 85, 102, 110, 697, 724, 744, 793, 816, 2648, 3122, 3541, 4467, 4535, 4585, 4643, 4693, 4754, 4850, 4908, 5066, 5126, 5178, 5236, 5294, 5346, 5419, 5471, 6211, 6790, 7023, 7063, 7110, 7141, 7191, 7746, 8421, 9186, 10319, 10469, 10511, 10563, 10629, 10698, 10755, 10795, 10831, 10869, 10894, 11020, 11045, 11078, 11096, 11159, 11160, 11179, 11249, 11250, 11251, 11371, 11437, 11537, 11607, 11674, 12221, 12280, 12344, 12403, 13320, 13646, 14468, 15911, 15943, 17020, 17133, 17187, 17240 | test_only | Test arenas, output buffers, and assertions. |
| `src/test_m68k_parse_util.c` | 216, 238, 246 | test_only | Test output cleanup and arena. |
| `src/test_m68k_render_plan.c` | 9 | test_only | Test result arena helper. |
| `src/test_platform_decompression.c` | 109 | test_only | Test JSON cleanup. |
| `src/tests/test_c_style.py` | 172 | test_only | Fixture text inside Python style test. |
| `src/util_arena.c` | 31, 33, 35, 50, 51, 72, 76, 88 | keep_heap_for_now | Core arena allocates/frees backing blocks and the arena object itself. |
| `src/util_arena.c` | 68 | keep_heap_for_now | `arena_create` implementation declaration, not a call site. |
| `src/util_arena.h` | 12 | keep_heap_for_now | `arena_create` prototype, not a call site. |

## PRD 001 Notes

- Arena Builder chunks and finalized arrays are arena-owned and add no raw heap allocation sites beyond the core arena backing allocation sites above.
- Builder allocations are visible through `ArenaStats` because every chunk and finalized output uses `arena_alloc`.
- Builders may be used with Workflow Arenas or Result Arenas. If a caller creates a builder after a Scratch Mark, both append chunks and finalized storage rewind with that mark; callers must not return or retain finalized pointers past that rewind.

## PRD 002 Notes

- `src/m68k_decode_ir.c`: direct raw heap allocation sites reduced from 6 (`realloc`, `calloc`, `free`) to 0; result lifetime is owned by `M68kDecodeIR.arena`.
- `src/m68k_fact_ir.c`: direct raw heap allocation sites reduced from 2 (`realloc`, `free`) to 0; result lifetime is owned by `M68kFactIR.arena`.
- Decode and facts tests assert arena stats visibility after result append/build operations.

## PRD 003 Notes

- `src/m68k_source_ir_render.c`: direct raw heap allocation sites reduced from 10 (`calloc`, `free`) to 0; temporary render indexes and include cache storage are owned by a local Workflow Arena.
- `src/m68k_source_file_emit.c`: direct raw heap allocation sites reduced from 27 (`calloc`, `free`) to 0; layout offsets, section writer slots, and intermediate writer output use workflow/result arenas.
- `src/platform_binary_io.c`: added `m68k_writer_build_arena` for arena-owned flattened writer output; existing `m68k_writer_build` remains the caller-freed output boundary.
- `src/m68k_analysis_render_lookup.c`: direct raw heap allocation sites reduced from 17 (`malloc`, `calloc`, `realloc`, `free`) to 0; render lookup temporary graphs, queues, and observations use local Workflow Arenas.

## Verification

Issue 0001 is documentation-only. Standard verification for implementation issues remains:

```powershell
cmd /c src\precommit.bat
```
