# Disassembly Progress

## Summary
| Metric | Value |
|--------|-------|
| Binary size | — |
| Bytes classified | 37802 |
| Coverage | — |
| Total entities | 414 |
| Entities typed | 307 |
| Entities named | 25 |
| Entities documented | 0 |
| Entities verified | 0 |
| Cross-refs resolved | 308 |

## Milestones
- [ ] Binary loaded and initial mechanical disassembly
- [ ] Entry point identified
- [ ] Main loop identified
- [ ] OS takeover/restore code documented
- [ ] Interrupt handlers identified
- [ ] Copper list(s) analyzed
- [ ] Sprite data located
- [ ] Bitplane/graphics data located
- [ ] Sound/music driver identified
- [ ] Input handling identified
- [ ] Game state structures identified
- [ ] Level data format understood
- [ ] Full round-trip reassembly passes

## Entity Status Breakdown

### Code Entities (307 total)
| Status | Count |
|--------|-------|
| unmapped | 65 |
| typed | 217 |
| named | 25 |
| documented | 0 |

### Data Entities (0 total)
| Status | Count |
|--------|-------|
| unmapped | 0 |
| typed | 0 |
| named | 0 |
| documented | 0 |

## Data Subtype Breakdown
(No data subtypes identified yet)

## Recent Activity
### 2026-05-03 Auto-analysis Campaign

Representative target: `amiga_hunk_genam`.
Comparators: `amiga_hunk_monam302`, Workbench corpus entries, Atari ST corpus entries.

Baseline corpus metrics:
- Corpus: 255 entries, 187757 xrefs, 323531 snippet rows, 150 type-flow rows, 29 unresolved typed-field rows.
- GenAm: opportunities 534, resolved typed accesses 2, numeric untyped accesses 452, typed storage 135.

Accepted implementation cycles:
- Generic helper return alias propagation: local helpers that call a typed OS API and return the result through an alias register now propagate that output type. Test: `facts_v2_render_asm_source_propagates_helper_return_alias_type`. Corpus delta: total resolved typed accesses 125 -> 127, numeric untyped accesses 39575 -> 39573. Workbench `amiga-hunk/c9e5dba3cbc2` improved 15 -> 17 resolved typed accesses. GenAm unchanged.
- Generic nested helper return alias propagation: helper summaries now inspect nested local helpers and conditional success fallthrough before `RTS`. Test: `facts_v2_render_asm_source_propagates_nested_helper_return_alias_type`. Corpus delta: total typed storage 1461 -> 1466. GenAm typed storage 135 -> 140, app-slot typed storage 7 -> 12.
- Generic API input prefix refinement: typed API input metadata can refine compatible prefix-derived register values and matching stored values, e.g. `MN` from `GetMsg` refined to `IO` when passed to `DoIO`. Test: `facts_v2_analysis_refines_prefix_storage_from_api_input`. Corpus delta: neutral on current corpus; no regressions.

Current corpus metrics after accepted cycles:
- Corpus: 255 entries, 187805 xrefs, 323531 snippet rows, 150 type-flow rows, 29 unresolved typed-field rows.
- GenAm: opportunities 534, resolved typed accesses 2, numeric untyped accesses 452, typed storage 140, app-slot typed storage 12, register typed storage 128.
- MonAm302: opportunities 518, resolved typed accesses 11, numeric untyped accesses 404, typed storage 66.

Remaining ranked gaps:
- GenAm `AllocMem` output storage without later typed access: most evidence is target-local allocated app structs, not reusable platform facts. Needs fixture/user annotations before typing.
- GenAm app-slot declarations for `TIMEVAL`/`IO` fields: analysis metadata is present, but source declarations remain coarse `RS.L`. This is renderer/source declaration work, not a generic analysis fact.
- Workbench `TC_Struct` tail offsets such as `$00AC`, `$00B0`, `$00B8`: likely private task/process extensions or mistyped bases. No generated platform container proves them.
- Atari high-volume gaps are numeric pointer chains rooted in globals, stack args, or unknown app data. No clean Atari platform metadata fix surfaced.
- Common Amiga calls audited with unknown outputs (`FreeMem`, `CloseLibrary`, `Forbid`, `ReplyMsg`, `AddHead`) are side-effect/no-output APIs; adding outputs would be wrong.

### 2026-05-03 Continuation

Review fixes:
- Kept the local helper-output recursion guard (`depth > 4`) in the nested helper propagation path.
- Made this progress log trackable by unignoring `targets/amiga_hunk_genam/progress.md`.

Accepted implementation cycle:
- Renderer/source declaration follow-through for typed app-slot regions. API-input app-slot structs are now emitted as inline `RS.B` regions when exact reproduction is preserved, and field references render through generated Amiga struct metadata. GenAm now renders `app_10A8 RS.B 8`, `app_10B0 RS.B 8`, `app_timer_device_iorequest RS.B 48`, `app_timer_device_iorequest+IO_DATA(a6)`, and `app_10B0+TV_MICRO(a6)`.
- Generic source include follow-through for symbolic addends. The renderer now scans `symbolic_addend_name` as well as the base symbol, so field expressions pull in `exec/io.i` and `devices/timer.i`; this fixed the temporary GenAm corpus parse failure on `app_timer_device_iorequest+IO_DATA(a6)`.
- Tests: `facts_v2_render_asm_source_renders_typed_app_slot_field_region` plus the existing `opendevice` source test.
- Corpus after fix: 255 entries, 187817 xrefs, 323531 snippet rows, 150 type-flow rows, 29 unresolved typed-field rows. `type-flow-check` vs `campaign-before-app-region-rendering.jsonl`: ok, no metric regressions.
- GenAm evidence: no `diagnostic:analysis_error`; app-slot typed regions 3, typed field refs 5, suggested regions 3, field gaps 13. Type-flow totals stayed neutral: opportunities 534, resolved typed accesses 2, typed storage 140.

Rejected / not clean cycles:
- GenAm `AllocMem` pointer fields remain the largest local storage-access gap. The later accesses look like target-owned allocated records, not reusable OS structs; target metadata would need fixture/user annotation.
- Workbench `DiskCopy`/handlers show many `AllocMem`-rooted records. These are app-local heap records; typing them generically would hardcode application layouts.
- Atari gaps are dominated by unknown pointer chains and stack/global roots. No shared OS metadata or typed-flow invariant was visible across GenAm comparators.
- Amiga API audit still shows calls such as `FreeMem`, `CloseLibrary`, `Forbid`, `ReplyMsg`, `AddHead`, `Move`, `RemPort`, and `SendIO`; inspected examples are void/side-effect APIs or calls with target-local bases, so output metadata would be incorrect.

Remaining ranked gaps:
- GenAm allocated app records after `AllocMem`: target-local struct inference only; needs annotation evidence.
- GenAm direct app-slot source declarations are now structurally improved, but promoted metadata is still API-evidence only. Committing target metadata requires fixture/user proof.
- MonAm302 `graphics.library/Move` example after a wrapper has no output metadata because `Move` is side-effect-only; the apparent pointer use is caller state.
- Workbench `TC_Struct` tail offsets remain private/custom-tail candidates with no generated container proof.
- Atari numeric pointer chains remain broad app-data recovery work, not a clean platform fact.
