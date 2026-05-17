# Arena Measurement Report

Parent proposal: historical arena allocation research

## Measurement Scope

The current linked-block arena was measured with explicit `ArenaStats` coverage in
`src/test_m68k_ir.c` and the migration inventory in `docs/c-arena-allocation-inventory.md`.
Timing data comes from `src/benchmark.json`, but timing is treated as noise unless paired with
allocation counts or arena stats.

## Arena Stats Baseline

`ArenaStats` now reports current and peak capacity, so wasted bytes are measurable as
`capacity - used`.

| Workflow | Used bytes | Capacity bytes | Wasted bytes | Blocks | Notes |
| --- | ---:| ---:| ---:| ---:| --- |
| Small mark/rewind, before rewind | 40 | 4096 | 4056 | 1 current / 1 total | Single minimum block. |
| Small mark/rewind, after rewind | 16 | 4096 | 4080 | 1 current / 1 total | Reuses same block. |
| Large transient allocation | 5032 | 9096 | 4064 | 2 current / 2 total | One 4096-byte block plus one 5000-byte block. |
| Same workflow after rewind | 32 | 4096 | 4064 | 1 current / 2 total | Tail block released; peak capacity remains visible. |
| Reset after large allocation | 0 | 4096 | 4096 | 1 current / 2 total | Reset keeps the head block and records peak capacity. |

## Hot Allocation Sites After PRD 001-004

| Area | Before | After | Current ownership |
| --- | ---:| ---:| --- |
| Decode IR result arrays | 6 raw sites | 0 | Result Arena |
| Facts IR result arrays | 2 raw sites | 0 | Result Arena |
| Source IR render temps | 10 raw sites | 0 | Workflow Arena |
| Source file emit temps | 27 raw sites | 0 | Workflow/Result Arenas |
| Render lookup temps | 17 raw sites | 0 | Workflow Arenas |
| HUNK parser temps | 45 raw sites | 0 | Workflow Arena, object Result Arena outputs |
| Platform disk workflow temps | 8 raw sites | 0 | Workflow Arena |
| Atari disk parser temps | 7 raw sites | 0 | Workflow Arena, analysis Result Arena outputs |

## Timing Noise

Recent full precommit timings varied by several seconds while allocation ownership stayed fixed.
The CDP suite also repeatedly showed transient browser/backend failures that passed on isolated
rerun. These are not allocator evidence.

## Finding

The linked-block arena is not a proven bottleneck from current evidence. The main measured issue
was ownership clarity, and PRD 001-004 removed the largest raw temporary allocation clusters without
changing public behavior. Advanced arena forms should only advance if a prototype demonstrates a
clear capacity, locality, or repeated-workflow win beyond benchmark noise.
