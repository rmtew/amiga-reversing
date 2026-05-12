# Growable Pool Prototype

Parent issue: `docs/issues/005-003-growable-pool-prototype.md`

## Prototype Scope

The prototype is test-only in `src/test_util_arena.c`.

It does not change production allocation behavior, default workflows, public C APIs, Python APIs, or
CLI behavior. The pool is backed by an existing `Arena`, so the prototype adds no production raw
heap allocation sites.

## Measurement

The representative workload repeatedly allocates 16 fixed-size temporary nodes for three rounds.
Plain arena allocation cannot free individual nodes, so it allocates every node in every round.
The pool grows once, returns freed slots to a free list, and reuses those slots in later rounds.

Each test node is 16 bytes.

| Allocator form | Rounds | Slots allocated from arena | Used bytes | Notes |
| --- | ---:| ---:| ---:| --- |
| Plain arena | 3 | 48 | 768 | One arena allocation per temporary node. |
| Growable pool prototype | 3 | 16 | 256 | One chunk, reused through free list after each round. |

The pool wins only when fixed-size objects are individually released and reused inside a workflow
that cannot rewind the whole arena yet. If a workflow can use a Scratch Mark around each round,
plain arena allocation is simpler and already reclaims the same memory shape.

## Fit Analysis

Object lifetime: pool slots can be returned individually before the broader workflow arena ends.
That helps for fixed-size nodes with interleaved allocate/free behavior.

Reset behavior: a pool reset can cheaply drop the free list and live count while keeping chunks in
the backing arena until the owning arena rewinds or resets. Full memory release still belongs to
the backing Arena lifetime.

Fragmentation: fixed-size slots avoid internal fragmentation between same-shaped nodes. The pool is
poor for mixed sizes; each size class needs its own pool or wastes slot space.

API complexity: callers need a pool object, an explicit object size, chunk sizing, and paired
allocate/free discipline. This is more complex than `arena_alloc` and creates double-free,
use-after-free, and wrong-pool-free hazards that arenas mostly avoid.

Failure modes: chunk growth can fail, wrong-size reuse corrupts callers, stale freed nodes can be
reused accidentally, and debug poisoning would need extra policy. Pool memory is not reclaimed until
the backing arena lifetime ends.

Expected benefit: useful for hot fixed-size work queues or graph nodes that churn within one
workflow. Not justified for append-only builders, result arrays, parser staging buffers, or code
paths already using Scratch Marks effectively.

## Decision

Do not migrate production code yet. Keep the pool as a measured option for a future fixed-size
temporary-node hotspot where Scratch Marks cannot express the lifetime cleanly.
