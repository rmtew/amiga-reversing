# Scratch and Frame Arena Fit Analysis

Parent issue: `docs/issues/005-004-scratch-frame-arena-fit-analysis.md`

## Evidence Base

Current evidence comes from:

- `docs/arena-measurement-report.md`
- `docs/arena-virtual-reserved-prototype.md`
- `docs/arena-growable-pool-prototype.md`
- `docs/c-arena-allocation-inventory.md`

The strongest measured result so far is ownership cleanup: PRD 001-004 removed large temporary raw
heap clusters by moving them to Workflow Arenas, Result Arenas, Scratch Marks, and Arena Builders.
No benchmark shows a production bottleneck that requires a new default allocator form.

## Per-Thread Scratch Arenas

Per-thread scratch arenas make transient allocation convenient but introduce lifetime ambiguity.
The project already has explicit `ArenaMark`/`arena_rewind` call sites where the owner and rollback
point are visible. A hidden thread scratch arena would make it easier to accidentally return or
store scratch-backed pointers in Result Arena objects.

Conflict avoidance requirements:

- Functions that call helpers using scratch need either a nested mark discipline or explicit scratch
  ownership in the call contract.
- Reentrant analysis/render code must not share the same scratch frame without a guaranteed mark.
- Async or UI-triggered workflows must not rely on thread identity as a proxy for operation lifetime.
- Debug builds would need poisoning or generation checks to catch retained scratch pointers.

Fit: weak for the current codebase. Explicit Workflow Arenas and Scratch Marks are more readable and
match the existing parser/render ownership model.

## Frame / Double-Buffer Arenas

Frame arenas work when a whole frame of temporary data can be discarded together, usually in repeated
loops with no retained pointers. Double-buffer arenas help when one previous frame must remain valid
while the next frame is built.

Potential matches:

| Workflow | Fit | Reason |
| --- | --- | --- |
| Web preview/render refresh | Maybe | Repeated operation, but preview text and render rows can escape as response/result data. |
| Facts/render lookup analysis | Weak | Multi-stage analysis has nested lifetimes and retained result pointers. |
| Disk/project browsing requests | Weak | Request-scoped allocation is already a Workflow Arena; outputs cross API boundaries. |
| Parser staging buffers | Weak | Scratch Marks already express local staging; object outputs are Result Arena owned. |
| Benchmark-only repeated runs | Maybe | Useful for measurement harnesses, not production behavior. |

Applicability depends on proving that a repeated workflow rebuilds the same temporary shape many
times and discards all previous temporary data at a fixed boundary. Current evidence shows ordinary
Workflow Arenas already provide that boundary for request-like work.

## Recommendation

Do not advance per-thread scratch arenas to implementation. They add hidden lifetime coupling and
conflict-avoidance rules without a measured bottleneck.

Do not advance frame or double-buffer arenas to production implementation yet. Keep them as a future
measurement option for a specific repeated workflow, such as preview rendering, if profiling shows
arena reset/rebuild overhead or allocation locality is material.

The current clean path remains:

- Result Arena for durable object/model outputs.
- Workflow Arena for operation-scoped temporary data.
- Scratch Marks for nested temporary staging.
- Arena Builder for append-and-flatten result construction.
